# V1-IB-D-2-B Authority Consistency Closure Checkpoint

Decision target:
`v1_ib_d_2_b_authority_consistency_closure_checkpoint_ready_for_counterpart_review`

## 1. Scope And Boundary

V1-IB-D-2-B is a report-only closure checkpoint for D-2 and D-2-A. It consolidates the accepted D-2 blocker-discovery evidence, the accepted D-2-A current-message report-routing authority fix, the now-passing D-2 tests, and the passing accepted baseline.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_2_b_authority_consistency_closure_checkpoint_2026-05-31.md`

No source files were edited. No tests were edited. No runtime behavior changed. No keyword, regex, synonym, punctuation, phrase, or no-alarm authority was added. No compatibility fallback was added. No browser/API UAT, packaging, staging, commit, push, deployment, strict enforcement, release closure, or V2 work occurred.

## 2. Accepted Evidence Consolidated

Accepted prerequisite chain:

- V1-IB-D-1 authority surface inventory and call-site map was accepted.
- V1-IB-D-2 authority consistency tests were accepted as blocker-discovery evidence.
- V1-IB-D-2-A current-message report-routing authority fix was accepted by Counterpart.

D-2 found that stale report-allow V1-IB metadata could still be accepted by report-routing checks for a different current user message. D-2-A fixed report-routing current-message identity and preserved the D-2 failing tests as regression coverage.

Current evidence:

- D-2 tests now pass.
- Accepted 157-test baseline still passes.
- Original D-2 stale report-authority blocker is closed.
- Stale report-allow metadata no longer skips pre-routing.
- Stale report-allow metadata no longer reaches compiled query.

## 3. Authority Model Confirmed

Only current, hash-matching, trace-safe, validated V1-IB contract authority can allow runtime business routing.

The following cannot authorize runtime business routing:

- stale V1-IB metadata
- boolean `report_routing_allowed=true` alone
- classifier/proposer evidence
- verifier evidence
- semantic-safe output
- legacy intent boundary
- rejected structural classifier
- report selector output
- compiled query output
- governed requery state
- model reasoning state
- visible-context state
- final-answer authority alone
- selected answer text
- prior context/artifacts
- trace metadata
- lexical/regex/keyword/synonym/punctuation/no-alarm logic

Report routing now aligns with the accepted visible-context and final-emission current-message proof pattern: route authority requires a current raw message, matching raw hash, matching normalized hash, valid validator status, trace-safe status, governed ERP mode, `authority_decision=allow_report`, safe replay, and no unsafe/mixed/ambiguous status.

## 4. Closed Blocker

Original blocker:

```text
current message: Show EC7H-ITEM-A item sales
stale allow contract source: Show EC7H-SUP-A payable status
previous behavior:
  _user_intent_boundary_report_routing_allowed(stale_boundary) == True
  _user_intent_boundary_pre_routing_response_required(stale_boundary) == False
  service reached compiled_first_turn
expected:
  boundary/control path
  no compiled query
  no report routing
```

D-2-A closure behavior:

- `_user_intent_boundary_report_routing_allowed(...)` now requires `raw_message`.
- Missing, blank, stale, normalized-mismatched, malformed, non-redaction-safe, non-governed, non-allow, replay-not-safe, unsafe, mixed, or ambiguous report metadata fails closed.
- `_user_intent_boundary_pre_routing_response_required(...)` cannot skip boundary response unless the report-routing helper proves current-message identity.
- Pre-frontdoor model reasoning/report authority and compiled fresh-query breakout now call the current-message-aware report helper.
- Stale allow-shaped metadata exposed in a boundary/control response is sanitized to fail-closed route flags.

Preserved D-2 regression tests now pass:

- `test_report_routing_helper_requires_current_contract_identity`
- `test_pre_routing_gate_must_not_skip_boundary_response_for_stale_allow_contract`
- `test_stale_report_allow_contract_must_not_reach_compiled_query`

## 5. Remaining Carry-Forward Risks

D-2-B does not claim V1-IB-D closure. Remaining bounded work:

- V1-IB-D-3 trace/diagnostic contract audit is still needed.
- V1-IB-D-4 legacy-authority retirement/quarantine plan is still needed.
- Old rejected structural classifier artifacts remain dirty/historical and must not be accepted as authority.
- The dirty worktree remains not package-ready.
- Browser/API UAT has not occurred.
- Packaging, release, deployment, and strict enforcement are not approved.
- Older legacy tests may still encode pre-V1-IB expectations and should be reviewed only in bounded, explicitly approved slices.

## 6. Next Recommended Step

Recommended next slice:

```text
V1-IB-D-3 trace and diagnostic contract audit
```

D-3 should be report/test-only first and should focus on trace payloads, diagnostic payloads, NBU shadow trace, runtime metadata, tool payloads, and leak-proofing. If D-3 finds a real source/runtime issue, it should preserve the failing evidence and request a separate narrow fix slice.

## 7. Verification

D-2 tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_cross_lane_contract_identity \
  ai_assistant_ui.tests.test_v1_ib_d_authority_surface_consistency \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_authority_consistency
```

Result:

```text
Ran 9 tests in 0.127s
OK
```

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

```text
Ran 157 tests in 0.408s
OK
```

Python compile:

```text
not_applicable_report_only_slice
```

Qwen enterprise guardrail:

```text
Qwen enterprise guardrail audit: PASS
```

Fake-Frappe service import:

```text
FAKE_FRAPPE_IMPORT_PASS
```

Direct assistant inventory:

```text
ACTIVE_RUNTIME_DIRECT_ASSISTANT_APPEND_COUNT=0
INVENTORY_COUNT=1
MIGRATED_AUTHORIZED_PATHS_LENGTH=27
```

Raw assistant append scan:

```text
FORMAL_RAW_SCAN=[
  ("impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py", 271),
  ("impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py", 327)
]
```

Report presence:

```text
report_present=PASS
```

Final git and artifact hygiene after report copy:

```text
git diff --check: PASS
git diff --cached --check: PASS
excluded_artifact_scan: PASS
staged_files=0
dirty_worktree_count_after_report=139
```

Report hygiene scan:

```text
report_only_scope=PASS
source_test_runtime_changes_in_d_2_b=0
forbidden_action_claims=0
stale_postcopy_note=0
```

## 8. Boundary Statement

V1-IB-D-2-B is not V1-IB-D closure. It closes the D-2 authority consistency checkpoint after D-2-A fixed the discovered stale report-routing authority blocker.

The worktree remains dirty and not package-ready.
