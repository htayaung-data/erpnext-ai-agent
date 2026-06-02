# V1-IB-D-4-A Legacy Restrict-Only Assertion Tests

Decision target:
`v1_ib_d_4_a_legacy_restrict_only_assertion_tests_ready_for_counterpart_review`

Date: 2026-05-31

## 1. Scope And Boundary

V1-IB-D-4-A is a tests-only evidence slice plus this governance report. It adds focused tests proving legacy `user_intent_boundary.py` output cannot authorize runtime business lanes or final emission. Legacy metadata may only restrict or fail closed.

No runtime source, existing test, validator, classifier, legacy boundary, structural classifier, import, packaging, staging, commit, push, deployment, browser/API UAT, strict enforcement, release-readiness, or V2 work occurred.

No keyword, regex, synonym, punctuation, phrase, or no-alarm authority was added. No compatibility fallback was added. No file was deleted, moved, renamed, or quarantined.

## 2. Files Changed

- Added `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_legacy_restrict_only.py`
- Added `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_a_legacy_restrict_only_assertion_tests_2026-05-31.md`

No source/runtime files were changed.

## 3. Tests Added

New test module:
`ai_assistant_ui.tests.test_v1_ib_d_legacy_restrict_only`

Test count:
8 tests

Coverage summary:

| Test | What it proves |
| --- | --- |
| `test_runtime_merge_keeps_legacy_allow_restrict_only` | V1-IB block/invalid/unsafe/mixed/ambiguous payloads remain blocked even when legacy metadata says allow. Legacy leak-only fields are redacted from merged metadata. |
| `test_runtime_merge_legacy_block_can_only_reduce_v1_ib_allow` | Legacy block can conservatively remove V1-IB allow flags, but legacy allow does not become the authority source when V1-IB already allows. |
| `test_service_blocking_v1_ib_dominates_legacy_allow_and_optimistic_lanes` | With V1-IB blocked and legacy/frontdoor/visible/requery/compiled/reasoning signals optimistic, service response remains `user_intent_boundary`; downstream lanes do not run or emit. |
| `test_service_missing_stale_malformed_or_invalid_v1_ib_fails_closed_despite_legacy_allow` | Missing, malformed, stale, and invalid V1-IB metadata fail closed even if legacy output says allow. |
| `test_final_emission_fallback_does_not_use_legacy_allow_to_emit_governed_answer` | Final emission fallback rebuilds/merges V1-IB and vetoes selected governed answer when V1-IB blocks, even if legacy builder is patched to allow. |
| `test_trace_metadata_keeps_legacy_allow_redacted_and_non_authoritative` | Legacy allow metadata remains redacted/non-authoritative in runtime metadata when V1-IB blocks. |
| `test_rejected_structural_classifier_is_not_runtime_authority_import` | Rejected `intent_boundary_structural_classifier.py` is not imported by runtime `qwen_chat` modules; it remains historical/test-only. |
| `test_safe_positive_control_is_v1_ib_authorized_not_legacy_authorized` | Current valid V1-IB allow plus legacy allow can proceed through safe report path, with authority source still marked as V1-IB; same safe-looking prompt without V1-IB authority fails closed. |

## 4. Authority Model Confirmed

Legacy metadata can only reduce or block authority. It cannot create or expand authority.

The tests prove legacy output cannot authorize:

- report routing
- visible-context reuse
- model reasoning activation
- governed requery
- compiled query
- final emission
- governed ERP answer mode
- trace metadata authority

The tests also confirm:

- `runtime_authority_source` remains `v1_ib_contract_validator` when V1-IB is the accepted authority path.
- Legacy `report_routing_allowed=true` and `context_reuse_allowed=true` do not matter unless V1-IB current-message authority allows the corresponding lane.
- Rejected structural classifier artifacts remain non-authority and are not runtime imports.
- Trace/runtime metadata may carry redaction-safe metadata only; legacy payload extras do not leak.

## 5. Leak Markers Used

The D-4-A tests used these markers and asserted they do not leak through blocked outputs/tool payloads:

- `LEAK_D4A_SELECTED_ANSWER`
- `LEAK_D4A_ROWS`
- `LEAK_D4A_ARTIFACT`
- `LEAK_D4A_VISIBLE`
- `LEAK_D4A_REASONING`
- `LEAK_D4A_COMPILED`
- `LEAK_D4A_REQUERY`
- `LEAK_D4A_LEGACY_ALLOW`

No blocker was found.

## 6. Verification

Focused D-4-A tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_legacy_restrict_only
```

Result:
`8 passed`

D-3/D-2 tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_authority_surface_consistency \
  ai_assistant_ui.tests.test_v1_ib_d_cross_lane_contract_identity \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_contract_audit
```

Result:
`8 passed`

Accepted baseline:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_prerouting \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_final_emission \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration \
  ai_assistant_ui.tests.test_v1_ib_runtime_final_emission_contract_veto \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_contract_validator \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_proposal_classifier \
  ai_assistant_ui.tests.test_authorized_emission_contracts \
  ai_assistant_ui.tests.test_service_control_authorized_emission_contracts
```

Result:
`157 passed`

Python compile:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m compileall -q \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_legacy_restrict_only.py
```

Result:
`PASS`

Final hygiene:

| Check | Result |
| --- | --- |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS: forbidden artifact status count `0` |
| Staged files count | PASS: `0` |
| Dirty worktree count | Recorded: `146` |
| Report hygiene scan | PASS: report present, decision target present, no placeholder verification results remain |

## 7. Carry-Forward

D-4-A does not close D-4 or V1-IB-D. It provides tests-only evidence that legacy boundary output is restrict-only and rejected structural classifier artifacts remain non-authority.

Remaining work still requires bounded QA/Counterpart approval:

- D-4-B rejected structural classifier quarantine/removal plan.
- D-4-C legacy lexical tests classification/alignment plan.
- D-4-D stale V1-R/Y/Z report archive/package-exclusion plan.
- D-4-E package-readiness cleanup plan after QA approval.

The worktree remains dirty and not package-ready. Browser/API UAT, packaging, staging, commit, push, deployment, strict enforcement, release readiness, enterprise closure, and V2 work remain out of scope.
