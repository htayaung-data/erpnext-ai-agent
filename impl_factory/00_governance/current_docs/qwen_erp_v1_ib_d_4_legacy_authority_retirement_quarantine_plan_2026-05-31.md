# V1-IB-D-4 Legacy-Authority Retirement / Quarantine Plan

Decision target:
`v1_ib_d_4_legacy_authority_retirement_quarantine_plan_ready_for_counterpart_review`

Date: 2026-05-31

## 1. Scope And Boundary

V1-IB-D-4 is a report-only retirement and quarantine planning slice. It inventories legacy authority-adjacent code, rejected scratch artifacts, old lexical tests, and stale governance reports so a future approved slice can retire or quarantine them safely.

No source, test, runtime, import, packaging, staging, commit, push, deployment, browser/API UAT, strict enforcement, release-readiness, or V2 work occurred in this slice.

This report does not delete, move, rename, rewrite, or disable any legacy file. It does not change runtime behavior. It does not add compatibility fallback. It does not add keyword, regex, synonym, punctuation, phrase, or no-alarm route authority.

## 2. Accepted Authority Model

Accepted V1-IB authority remains unchanged:

- `IntentBoundaryContract` is the sole runtime route authority.
- The V1-IB proposal classifier is evidence only.
- Proposer, verifier, proof, replay, semantic-safe, and model outputs are evidence or restrictive signals only.
- Legacy `user_intent_boundary.py` may only restrict or fail closed. It may not authorize report routing, visible-context reuse, model reasoning, final emission, or governed ERP answer mode.
- Old rejected `intent_boundary_structural_classifier.py` is not accepted authority.
- Lexical, regex, keyword, synonym, punctuation, phrase, and no-alarm logic may extract identifiers, support redaction, validate spans/schema, raise conservative alarms, or contribute restrictive evidence. It must never grant route authority.
- Trace and diagnostic metadata are non-authoritative and redaction-safe only.

The following fields may only be allowed by current, hash-matching, trace-safe, validated V1-IB contract authority:

- `report_routing_allowed=true`
- `context_reuse_allowed=true`
- `model_reasoning_allowed=true`
- `final_emission_allowed=true`
- `required_answer_mode=governed_erp_answer`
- `authority_decision=allow_report`

## 3. Legacy Surface Inventory

| Surface | Status | Runtime import | Test import | Can authorize today | Temporary retention reason | Future action | Risk if left unclassified |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `qwen_chat/user_intent_boundary.py` | Legacy lexical/structural boundary module. Active only as restrict/fail-closed companion metadata. | Yes. Imported by `service.py` and fallback path in `authorized_emission.py`. | Yes. Multiple legacy tests import it directly. | No accepted allow authority. Runtime merges it under V1-IB through `merge_v1_ib_with_legacy_boundary`; it can restrict a V1-IB allow but must not expand a V1-IB block. | Retained until tests prove all V1-IB lanes remain safe without treating legacy output as authority. | D-4-A restrict-only assertion tests, then D-4-C classification/alignment, then future quarantine/retirement only with QA approval. | Future developers could mistake legacy booleans or category labels for accepted allow authority. |
| `qwen_chat/intent_boundary_structural_classifier.py` | Rejected historical structural classifier scratch. | No runtime import found in `qwen_chat/*.py` static scan. | Yes. Imported by `tests/test_v1_ib_structural_classifier.py`. | No. Not on accepted runtime path. | Retained only as historical dirty-worktree artifact until packaging cleanup is approved. | D-4-B quarantine/removal plan; do not use as release evidence. | Could be confused with accepted V1-IB-B proposal classifier if not clearly quarantined. |
| `tests/test_v1_ib_structural_classifier.py` | Historical test for rejected structural classifier. | No. | Yes, imports rejected classifier. | No. Tests cannot authorize runtime. | Historical scratch until D-4-B decides quarantine/delete/archive. | D-4-B classify as rejected scratch, then archive or remove in package-cleanup branch after approval. | Could be misreported as accepted V1-IB-B evidence. |
| `tests/test_user_intent_boundary_lexical_fragility.py` | Legacy lexical fragility tests. | No. | Yes, imports `user_intent_boundary.py`. | No. | Retained as historical regression context only. | D-4-C decide whether to rewrite as V1-IB evidence or quarantine as old V1-R evidence. | Encourages patch-loop thinking if treated as current release proof. |
| `tests/test_user_intent_boundary_prerouting_gate.py` | Legacy pre-routing expectations around old boundary helper behavior. | No. | Yes, imports `service.py` and `user_intent_boundary.py`. | No. | Some expectations may be useful as restrictive regression history, but not as allow-authority proof. | D-4-C align or quarantine after current V1-IB assertion coverage exists. | May encode pre-V1-IB raw-message-less compatibility assumptions. |
| `tests/test_user_intent_boundary_long_context_regression.py` | Legacy long-context regression tests. | No. | Yes, imports `service.py` and `user_intent_boundary.py`. | No. | Historical context for context-bleed risks. | D-4-C classify/alignment. Known optional legacy assumptions should not block accepted V1-IB baseline unless separately approved. | Could conflict with accepted fail-closed helper semantics if run as release baseline without alignment. |
| `tests/test_user_intent_boundary_contracts.py` | Legacy direct contract tests for `user_intent_boundary.py`. | No. | Yes. | No. | Historical coverage of old lexical categories. | D-4-C decide whether any assertions should survive as restrict-only documentation. | May imply legacy contract validity is accepted runtime authority. |
| `tests/test_user_intent_boundary_final_emission_veto.py` | Legacy final-emission veto regression tests. | No direct runtime effect. | Yes, imports old boundary and authorized emission. | No. | Some leak/veto expectations may overlap with accepted V1-IB veto evidence. | D-4-C align with current V1-IB final-emission authority or quarantine old assumptions. | Could duplicate or contradict accepted V1-IB final-emission tests if not classified. |
| Old V1-R-Y lexical hardening reports | Historical governance chain for lexical fixes. | No. | No. | No. | Historical audit trail only. | D-4-D stale report archive/package-exclusion plan. | Could be mistaken for current release authority model despite V1-IB replacing the lexical route model. |
| Old V1-IB-B/B-A/B-B structural classifier reports from 2026-05-28 | Rejected structural classifier history. | No. | No. | No. | Historical scratch trail only. | D-4-D classify as rejected and package-excluded historical docs. | Could obscure accepted V1-IB-B proposal-classifier closure if not labeled. |
| `service.py` helper family `_user_intent_boundary_*` | Active V1-IB runtime gates and redaction helpers. | Runtime code. | Exercised by V1-IB tests. | Yes, but only when helpers verify current V1-IB contract identity and fields. Legacy metadata is not sufficient. | Required current runtime authority surface. | D-4-A add/confirm restrict-only assertions for legacy metadata dominance. | If future edits weaken current-message proof, stale legacy/V1-IB metadata could re-open prior bypass classes. |
| `authorized_emission.py` final-emission V1-IB fallback path | Active final-emission veto authority path. | Runtime code. | Exercised by accepted V1-IB final-emission tests. | Yes, but only through current hash-matching V1-IB contract or rebuilt V1-IB boundary. | Required to fail closed when carried contract is missing or stale. | D-4-A should include legacy allow cannot override V1-IB final-emission veto assertions if not already sufficient. | Future maintainers may misread fallback legacy boundary as allow authority rather than merge input. |

## 4. Runtime Import / Authority Audit

Static import scan results:

- `service.py` imports `build_user_intent_boundary_contract` at line 50 and `merge_v1_ib_with_legacy_boundary` at line 55.
- `handle_qwen_user_message` builds legacy metadata at line 4158, builds V1-IB runtime boundary at line 4159, and merges at lines 4160-4163.
- `authorized_emission.py` imports legacy builder only inside `_user_intent_boundary_for_final_emission_veto` fallback at lines 405-409 after rejecting carried stale/non-current candidates.
- `intent_boundary_runtime_integration.py` defines `merge_v1_ib_with_legacy_boundary` at line 267.
- `intent_boundary_structural_classifier.py` has no runtime import found in the `qwen_chat` runtime static scan. It is imported by `tests/test_v1_ib_structural_classifier.py` only.

Current merge behavior:

- `merge_v1_ib_with_legacy_boundary` copies the V1-IB runtime payload as the primary payload.
- It stores only redacted legacy fields in `legacy_user_intent_boundary_metadata`.
- It sets `runtime_authority_source` to `v1_ib_contract_validator`.
- If V1-IB allows report routing but legacy metadata blocks report routing, the merge changes the payload to a clarification/block state.
- If V1-IB allows context reuse but legacy metadata blocks context reuse, the merge removes context/model/final authority and blocks.
- There is no observed merge path where legacy metadata turns a V1-IB block into allow.

Current service gate behavior:

- `_user_intent_boundary_context_reuse_allowed` requires a non-empty current raw message, hash match, normalized hash match, `validator_status=valid`, `trace_redaction_status=safe`, `safe_followup_intent=true`, no unsafe/mixed/ambiguous flags, and `context_reuse_allowed=true`.
- `_user_intent_boundary_report_routing_allowed` requires a non-empty current raw message, hash match, normalized hash match, `validator_status=valid`, `trace_redaction_status=safe`, `report_routing_allowed=true`, governed ERP answer mode, `authority_decision=allow_report`, replay-safe final decision, and no unsafe/mixed/ambiguous flags.
- `_user_intent_boundary_pre_routing_response_required` fails closed unless current report-routing authority is proven.

Current final-emission behavior:

- `_user_intent_boundary_for_final_emission_veto` accepts a carried boundary only if it matches the current interaction raw/normalized hashes and is trace-redaction safe.
- If no current carried boundary is available, it rebuilds V1-IB runtime boundary and merges legacy metadata.
- Final emission veto logic then blocks business answer types unless current V1-IB authority permits the selected lane.

Accepted baseline relationship:

- The accepted V1-IB baseline does not include old `test_user_intent_boundary_*` lexical fragility tests or `test_v1_ib_structural_classifier.py`.
- Accepted baseline modules are V1-IB runtime, final-emission veto, contract validator, proposal classifier, authorized-emission alignment, and service-control authorized-emission tests.
- Old reports are governance history only. They are not runtime imports and are not package approval.

## 5. Future Retirement / Quarantine Plan

### D-4-A: Legacy Restrict-Only Assertion Tests

Recommended next slice. Tests-only.

Goal:
prove legacy `user_intent_boundary.py` output cannot authorize any V1-IB lane and can only restrict/fail closed.

Suggested assertions:

- Legacy allow plus V1-IB block still blocks pre-routing.
- Legacy allow plus V1-IB block does not call report selector, compiled query, governed requery, visible context, model reasoning, or final emission.
- Legacy allow plus stale V1-IB metadata fails closed.
- Legacy allow plus missing current raw-message proof fails closed.
- Legacy block plus V1-IB allow remains conservative unless accepted tests prove a safe transition.
- Authorized emission fallback cannot use legacy allow to emit governed business output.

### D-4-B: Rejected Structural Classifier Quarantine / Removal Plan

Report-only first, then cleanup only if approved.

Goal:
classify `intent_boundary_structural_classifier.py` and `test_v1_ib_structural_classifier.py` as rejected historical scratch, not accepted V1-IB-B evidence.

Future options:

- Rename/archive in a package-excluded historical directory after package-branch approval.
- Delete only in an approved cleanup branch with explicit diff review.
- Replace release references with accepted proposal-classifier files and reports.

### D-4-C: Legacy Lexical Tests Classification / Alignment Plan

Report/test-only first.

Goal:
separate useful restrict-only regression assertions from obsolete pre-V1-IB compatibility expectations.

Candidate files:

- `tests/test_user_intent_boundary_contracts.py`
- `tests/test_user_intent_boundary_final_emission_veto.py`
- `tests/test_user_intent_boundary_lexical_fragility.py`
- `tests/test_user_intent_boundary_long_context_regression.py`
- `tests/test_user_intent_boundary_prerouting_gate.py`

Allowed future outcomes after approval:

- Rewrite selected tests to assert legacy restrict-only behavior under V1-IB.
- Move old lexical patch-loop tests out of the accepted release baseline.
- Quarantine obsolete tests as historical evidence, not current acceptance evidence.

### D-4-D: Stale V1-R/Y/Z Report Archive / Package-Exclusion Plan

Report-only first.

Goal:
label old V1-R-Y lexical hardening reports and rejected 2026-05-28 V1-IB-B structural classifier reports as historical, not current authority model.

Static scan found 31 `qwen_erp_v1_r_y*.md` reports and no `qwen_erp_v1_r_z*.md` reports in current docs.

Rejected V1-IB-B structural history found:

- `qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
- `qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
- `qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`

Accepted V1-IB-B proposal-classifier reports remain separate and should stay as current evidence:

- `qwen_erp_v1_ib_b_0_deterministic_classifier_restart_plan_2026-05-29.md`
- `qwen_erp_v1_ib_b_1_proposal_classifier_implementation_boundary_request_2026-05-29.md`
- `qwen_erp_v1_ib_b_proposal_classifier_implementation_2026-05-29.md`
- `qwen_erp_v1_ib_b_a_proposal_classifier_evidence_strictness_fix_2026-05-29.md`
- `qwen_erp_v1_ib_b_b_proposal_classifier_closure_checkpoint_2026-05-29.md`

### D-4-E: Package-Readiness Cleanup Plan

Report-only first, only after QA approves D-4-A/B/C/D outcomes.

Goal:
prepare a package-safe cleanup boundary after V1-IB-D closure, not during D-4.

Rules:

- No cleanup from the current dirty worktree without explicit package branch/refresh approval.
- No deletion that changes accepted V1-IB runtime behavior.
- No silent removal of tests.
- No staging, commit, push, package, deploy, or release-readiness claim until QA approves a package-readiness slice.

## 6. Non-Negotiable Rules For Future Retirement

- Do not remove legacy surfaces without tests proving V1-IB lanes still pass and still fail closed.
- Do not delete from the dirty worktree without package branch/refresh approval.
- Do not reintroduce lexical, regex, synonym, punctuation, phrase, or no-alarm logic as authority.
- Do not silently delete legacy tests.
- Do not treat old structural classifier tests as accepted proposal-classifier evidence.
- Do not treat old V1-R/Y lexical reports as current V1-IB release evidence.
- Quarantine old lexical artifacts as historical or rewrite them as V1-IB restrict-only evidence.
- Runtime cleanup must be separately approved by QA/Counterpart.

## 7. Carry-Forward Risks

- Legacy `user_intent_boundary.py` is still physically imported by runtime. Current merge behavior is restrict-only, but this should be pinned by D-4-A tests before any closure claim.
- Rejected `intent_boundary_structural_classifier.py` remains in the tree and is test-imported by historical tests.
- Old V1-R-Y lexical reports remain in `current_docs` and can confuse release evidence unless archived or marked historical later.
- Old user-intent-boundary tests may encode pre-V1-IB assumptions and should not be folded into accepted baseline without bounded alignment.
- Dirty worktree remains not package-ready.
- No browser/API UAT, packaging, deployment, strict enforcement, release readiness, or V2 work has occurred.

## 8. Next Recommended Step

Recommend:
`V1-IB-D-4-A legacy restrict-only assertion tests`

Reason:
the audit did not find a direct runtime import of the rejected structural classifier, but it did confirm legacy `user_intent_boundary.py` remains in active runtime merge/fallback paths. The safest next move is a tests-only slice proving legacy output cannot authorize report routing, visible context, model reasoning, governed requery, compiled query, final emission, or trace metadata.

Do not proceed directly to D-5 formal closure until D-4-A either passes or documents a blocker.

## 9. Verification

Commands/results for D-4:

| Check | Result |
| --- | --- |
| Report present | PASS: `qwen_erp_v1_ib_d_4_legacy_authority_retirement_quarantine_plan_2026-05-31.md` exists |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS: forbidden artifact status count `0` |
| Staged files count | PASS: `0` |
| Dirty worktree count | Recorded: `144` |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |
| Static legacy import scan | PASS: structural classifier runtime import not found; legacy boundary runtime import found and classified restrict-only |

Static scan details:

- `intent_boundary_structural_classifier` appears in `tests/test_v1_ib_structural_classifier.py` only.
- `build_user_intent_boundary_contract` appears in `service.py`, `authorized_emission.py`, `user_intent_boundary.py`, legacy tests, and V1-IB tests that mock legacy allow to prove V1-IB dominance.
- `merge_v1_ib_with_legacy_boundary` appears in `service.py`, `authorized_emission.py`, `intent_boundary_runtime_integration.py`, and V1-IB tests.
- Raw assistant append sinks remain only in `authorized_emission.py` at lines 271 and 327.
