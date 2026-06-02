# V1-IB-D-1 Authority Surface Inventory And Call-Site Map

Decision target:
`v1_ib_d_1_authority_surface_inventory_call_site_map_ready_for_counterpart_review`

## 1. Scope And Boundary

V1-IB-D-1 is a report-only inventory slice. It maps runtime authority surfaces, relevant call sites, legacy/rejected authority paths, and D-2 bypass hypotheses.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_1_authority_surface_inventory_call_site_map_2026-05-31.md`

No source files were edited. No test files were edited. No runtime behavior changed. No runtime gates, compatibility fallbacks, keyword/regex/synonym/punctuation authority, browser/API UAT, staging, commit, push, packaging, deployment, V2 work, or D-2 implementation occurred.

## 2. Accepted Authority Model

Accepted basis:

- V1-IB-A contract/validator foundation is accepted.
- V1-IB-B proposal classifier is accepted as evidence-only.
- V1-IB-C runtime integration is formally closed as runtime integration evidence.
- V1-IB-D-0 planning is accepted by Architecture/Counterpart.

D-1 does not change the accepted authority model:

- Only a current, validated `IntentBoundaryContract` may authorize route behavior.
- Classifier/proposer output may provide evidence only.
- Verifier output may provide consistency/provenance evidence only.
- Semantic-safe/model output may not authorize.
- Enterprise model answer text may not authorize.
- Final-answer authority alone may not authorize.
- Visible-context state may not authorize.
- Report selector output may not authorize.
- Compiled-query output may not authorize.
- Legacy user-intent boundary output may restrict/fail closed only.
- Lexical, regex, keyword, punctuation, synonym, or no-alarm logic may not authorize.
- Trace metadata may not authorize.
- Prior conversation context may not authorize.
- Selected rows, artifacts, narratives, grounded evidence, or rendered payloads may not authorize.

Lexical/token logic remains limited to identifier extraction, span/schema validation, trace redaction, conservative alarms, and fail-closed validation support. It must never grant `report_routing_allowed=true`, `context_reuse_allowed=true`, `model_reasoning_allowed=true`, `final_emission_allowed=true`, `required_answer_mode=governed_erp_answer`, or `authority_decision=allow_report`.

## 3. Call-Site Inventory

### Runtime Integration Authority Glue

| File | Function / Line | Authority Decision Influenced | Input Trusted | V1-IB Gate | Can Emit/Route/Trace | Classification |
|---|---:|---|---|---|---|---|
| `intent_boundary_runtime_integration.py` | `_fail_closed_boundary` line 136 | Fail-closed route flags on missing/exception paths | Raw message only for hashes | all route flags forced false, `authority_decision=block` | Trace metadata only | accepted |
| `intent_boundary_runtime_integration.py` | `_normalize_validated_boundary` line 164 | Normalizes validator route flags | Validator `IntentBoundaryContract` payload | `validator_status`, `trace_redaction_status`, replay safe, `required_answer_mode`, `authority_decision`, unsafe/ambiguous flags | Produces runtime contract metadata | accepted |
| `intent_boundary_runtime_integration.py` | `build_v1_ib_runtime_boundary` line 229 | Builds runtime boundary from proposal + validator | Raw user message, proposal builder, validator | Validator-owned normalized route fields | Metadata only | accepted |
| `intent_boundary_runtime_integration.py` | `merge_v1_ib_with_legacy_boundary` line 267 | Merges legacy boundary restrictively | V1-IB boundary and legacy metadata | V1-IB remains source; legacy can only remove allow | Metadata only | accepted restrict-only |
| `intent_boundary_runtime_integration.py` | `v1_ib_runtime_contract_metadata` line 312 | Redaction-safe trace metadata | Current merged boundary | Metadata field whitelist | Trace/tool payload metadata | accepted |

### Service Runtime Entry And Gates

| File | Function / Line | Authority Decision Influenced | Input Trusted | V1-IB Gate | Can Emit/Route/Trace | Classification |
|---|---:|---|---|---|---|---|
| `service.py` | imports line 33-54 | Connects service to authorized emission, legacy boundary, and V1-IB runtime boundary | Imported helpers | none directly | Enables later authority flow | accepted |
| `service.py` | `_user_intent_boundary_matches_current_message` line 724 | Current-message proof helper | Boundary hash fields + raw message | type, raw hash, normalized hash | No emit | accepted |
| `service.py` | `_user_intent_boundary_has_unsafe_or_ambiguous_intent` line 742 | Conservative context block helper | V1-IB unsafe/ambiguous fields | decision/advice/action/policy/mixed/ambiguity | No emit | accepted |
| `service.py` | `_user_intent_boundary_context_reuse_allowed` line 762 | Visible-context/context reuse authorization | Current boundary + raw message | type, hashes, `validator_status=valid`, trace safe, safe follow-up, no unsafe/mixed/ambiguous, `context_reuse_allowed` | No emit directly; gates visible context | accepted |
| `service.py` | `_user_intent_boundary_report_routing_allowed` line 784 | Report route flag check | Merged V1-IB runtime boundary | `report_routing_allowed` boolean from normalized boundary | No emit directly; gates report/model decisions | accepted but D-2 should assert consumers only receive current normalized boundary |
| `service.py` | `_user_intent_boundary_pre_routing_response_required` line 790 | Pre-routing block decision | Merged V1-IB boundary + pending clarification signal | report-routing allow absent means boundary response | May trigger control/policy/clarification emission | accepted |
| `service.py` | `_visible_context_followup_should_preempt_clarification` line 807 | Visible-context preemption | Message + current boundary | strict context reuse helper | No emit directly; gates visible context | accepted |
| `service.py` | `_artifact_boundary_should_yield_to_visible_context` line 821 | Artifact boundary yielding | Entity drilldown/skips + boundary | strict visible-context helper | No emit directly | accepted |
| `service.py` | `_compiled_fresh_query_should_yield_to_visible_context` line 842 | Compiled query yields to visible context | Message + boundary | strict visible-context helper | No emit directly | accepted |
| `service.py` | `_runtime_gate_should_yield_to_visible_context` line 857 | Runtime gate yielding | Message + boundary | strict visible-context helper | No emit directly | accepted |
| `service.py` | `_nbu_presentation_should_yield_to_local_or_visible_context` line 872 | NBU presentation yielding | Presentation request + boundary | strict visible-context helper or local projection flag | No emit directly | risk-bearing: local projection path is separate and should remain restrictive |
| `service.py` | `_append_tool_payload` line 1185 | Tool/trace append sink | Payload from runtime lanes | Redaction depends on caller contracts | Exposes trace/tool payload | accepted, needs D-3 diagnostic audit |
| `service.py` | `_emit_user_intent_boundary_pre_routing_response` line 3597 | Boundary/control/clarification response | Current V1-IB boundary | `required_answer_mode`, category, reason | Emits authorized control/policy response | accepted |
| `service.py` | `handle_qwen_user_message` line 4057 | Runtime entry point | Raw message, session | Builds legacy then V1-IB, merges restrictively | Can reach all lanes | accepted |
| `service.py` | `handle_qwen_user_message` lines 4065-4071 | Builds legacy + V1-IB and merged boundary | Raw message | `build_v1_ib_runtime_boundary`, `merge_v1_ib_with_legacy_boundary` | Metadata only at this point | accepted |
| `service.py` | `v1_ib_runtime_tool_payload` line 4071 | Trace metadata construction | Merged boundary | metadata whitelist | Tool payload metadata | accepted |
| `service.py` | NBU shadow trace build lines 4137-4151 | Early trace/diagnostic path | Raw/effective message, prior context | No route authority; expected redaction-safe trace only | Exposes tool payload if non-empty | risk-bearing for D-3 trace audit |
| `service.py` | early visible-context trace gate lines 4154-4181 | Visible-context trace activation | Current boundary + raw message | strict context reuse helper | Can emit visible-context answer | accepted after C-3-4-B/B-A |
| `service.py` | pre-frontdoor reasoning condition lines 4288-4293 | Early reasoning activation | Reasoning rollout, grounded state, current boundary | strict context reuse + report-routing allow | Can later invoke reasoning | accepted; D-2 should assert same contract identity |
| `service.py` | artifact local refinement lines 4422-4435 | Local artifact/refinement evidence | Grounded turn + current boundary | strict context reuse helper | Can influence later routing/context | accepted restrictively; D-2 should cover |
| `service.py` | `evaluate_frontdoor_lane` line 4480 | Report selector/frontdoor evidence | Message, recent messages, grounding | Pre-routing gate occurs later before emission | Evidence only until `handle_frontdoor_turn` | risk-bearing: frontdoor evidence computed before V1-IB pre-routing gate |
| `service.py` | pre-routing gate lines 4665-4679 | Main V1-IB pre-route stop | Merged boundary | `_user_intent_boundary_pre_routing_response_required` | Emits boundary/control/clarification | accepted |
| `service.py` | semantic follow-up interpretation lines 4698-4728 | Semantic follow-up evidence | Grounding, message, current boundary | strict context reuse helper | Evidence only | accepted evidence-only |
| `service.py` | artifact/context preserve lines 4772-4841 | Context isolation/preservation | Current boundary, grounded/artifact state | strict context reuse helper | Can influence context/routing | accepted, D-2 should test consistency |
| `service.py` | visible/requery authority basis lines 4892-4932 | Visible-context and governed requery preconditions | Current boundary, frontdoor state, context state | visible-context helper result | Can emit visible-context or requery answer | accepted after C-3 evidence; still D-2 candidate |
| `service.py` | governed requery activation lines 4932-4956 | Governed requery | Context/artifact, V1-IB-derived continuation conditions | indirect via `visible_context_followup_has_authority` and pre-routing having passed | Can emit governed requery answer | risk-bearing: D-2 should prove no activation after V1-IB block |
| `service.py` | compiled fresh query breakout lines 4962-4975 | Compiled/report query path | Runtime message, rollout, frontdoor state | `_user_intent_boundary_report_routing_allowed`; visible-context yield helper | Can reach compiled query | accepted with C-3 tests; D-2 should assert current contract identity |
| `service.py` | `handle_frontdoor_turn` line 5118 | Report selector/frontdoor emission | Frontdoor semantic result + contract | Only after pre-routing gate | Can emit report/frontdoor answer | accepted with risk note: frontdoor cannot be authority |
| `service.py` | pending clarification path line 5147 | Clarification continuation | Pending signal, clarification contracts | Not route authority; can preempt runtime | Can emit clarification response | accepted restrict-only |
| `service.py` | visible context follow-up line 5348-5373 | Visible-context emission | Current boundary + prior context | strict visible-context helper | Can emit visible-context answer | accepted |
| `service.py` | model reasoning line 5374-5444 | Reasoning activation and emission | Rollout, grounded state, semantic result | should be reached only after pre-routing and V1-IB-allowed context/report conditions | Can emit model reasoning answer | risk-bearing for D-2 consistency assertions |
| `service.py` | capability requery/frontdoor line 5608-5676 | Requery/frontdoor continuation | Follow-up resolution, continuation, frontdoor result | Needs prior gates and accepted C-3 blockers | Can emit frontdoor/requery answer | risk-bearing for D-2 |
| `service.py` | tool trace append lines 5718-5738 | Runtime trace/metadata append | Many runtime contracts | Redaction-safe callers expected | Exposes tool payloads | D-3 trace audit |
| `service.py` | NBU presentation line 5771-5809 | NBU presentation response | Follow-up resolution/context | `_nbu_presentation_should_yield...` includes V1-IB visible-context yielding | Can emit presentation | risk-bearing; D-2/D-3 |
| `service.py` | artifact boundary line 5865-5892 | Visible context before artifact boundary | Current boundary + artifact state | strict visible-context helper | Can emit visible-context answer | accepted |
| `service.py` | local transform lines 5932-6025 | Local grounded transform | Follow-up resolution/context | Earlier V1-IB gate required for business path | Can return local transform | risk-bearing for legacy/diagnostic audit |
| `service.py` | runtime gate visible-context line 6027-6052 | Visible context before runtime gate | Current boundary | strict visible-context helper | Can emit visible-context answer | accepted |
| `service.py` | runtime gate / compiled path line 6125-6164 | Runtime gate and compiled execution | Runtime message, followup, frontdoor, compiled rollout | Prior pre-routing and report-route gates | Can emit compiled/runtime answer | accepted, D-2 consistency target |
| `service.py` | `handle_legacy_runtime_turn` line 6165 | Legacy runtime fallback | Runtime message and latest payloads | Reached only after prior gates; final emission should still veto business conflicts | Can emit legacy runtime answer | unresolved/risk-bearing: needs D-2/D-4 retirement plan |

### Final Emission

| File | Function / Line | Authority Decision Influenced | Input Trusted | V1-IB Gate | Can Emit/Route/Trace | Classification |
|---|---:|---|---|---|---|---|
| `authorized_emission.py` | `_sanitize_user_intent_veto_audit_payload` line 340 | Veto payload sanitization | Runtime trace veto marker | `user_intent_final_emission_veto` | Removes selected answer/rows/artifacts/rendered/narrative/grounded evidence from audit payload | accepted |
| `authorized_emission.py` | `_interaction_raw_message_for_user_intent_veto` line 358 | Current raw message extraction | Interaction contract | raw message required for hash match | No emit | accepted |
| `authorized_emission.py` | `_user_intent_boundary_matches_current_message` line 364 | Carried contract currentness | Boundary + raw message | trace safe, raw hash, normalized hash | No emit | accepted after C-2-A |
| `authorized_emission.py` | `_user_intent_boundary_for_final_emission_veto` line 381 | Finds current contract or rebuilds fail-closed | Authority context, runtime trace, pre-assistant payloads, raw message | current hash match; rebuilds V1-IB + legacy if missing/stale | No emit directly | accepted |
| `authorized_emission.py` | `_user_intent_final_emission_veto_required` line 415 | Final business answer veto | Answer type + V1-IB boundary | governed report/context route flags | Veto decision | accepted |
| `authorized_emission.py` | `_user_intent_final_emission_veto_payload` line 447 | Veto trace payload | Current boundary | V1-IB fields | Trace/control payload | accepted |
| `authorized_emission.py` | `emit_authorized_assistant_answer` line 495 | Final authorized emission | Selected answer, answer type, contracts, trace | current V1-IB boundary from `_user_intent_boundary_for_final_emission_veto` | Emits assistant answer or veto boundary | accepted |
| `authorized_emission.py` | veto branch lines 541-598 | Vetoed final answer emission | Current V1-IB boundary | `required_answer_mode` and route flags | Emits safe policy/control answer; redacts selected payloads | accepted |

### Contract / Validator Authority

| File | Function / Line | Authority Decision Influenced | Input Trusted | V1-IB Gate | Can Emit/Route/Trace | Classification |
|---|---:|---|---|---|---|---|
| `intent_boundary_contract.py` | `IntentBoundaryContract` dataclass line 632 | Contract payload shape | Validator-owned construction | contract fields | No emit | accepted |
| `intent_boundary_contract.py` | `detect_raw_message_unsafe_evidence` line 1051 | Conservative raw-message alarm evidence | Normalized message | restrict-only | No emit | accepted restrict-only |
| `intent_boundary_contract.py` | `_validate_validator_owned_raw_message_analysis` line 1677 | Stored analysis audit prerequisite | Registries/evidence | must match raw hashes and proof evidence | No emit | accepted provenance-only |
| `intent_boundary_contract.py` | `_validate_raw_message_analysis_execution` line 1803 | Execution proof audit | Execution registry/proof | status/source/hash/attestation/replay checks | No emit | accepted provenance-only |
| `intent_boundary_contract.py` | `_positive_replayed_safety_classification` line 1991 | Positive safe factual replay subset | Normalized message + targets | narrow positive safe factual lookup only | No emit | accepted authority source inside validator |
| `intent_boundary_contract.py` | `_replay_raw_message_safety` line 2015 | Validator-owned replay | Raw/normalized message + approved analyzer entry | replay source/version/config/artifact + positive safety | No emit | accepted authority source inside validator |
| `intent_boundary_contract.py` | `_validate_replayed_raw_message_safety` line 2094 | Replay/proof consistency | Replay result, proof, analysis | replay must be safe and match evidence | No emit | accepted |
| `intent_boundary_contract.py` | `_validate_clause_role_verification` line 2476 | Role verifier provenance/consistency | Verifier envelope and registry | consistency only; cannot authorize alone | No emit | accepted evidence/provenance |
| `intent_boundary_contract.py` | `_semantic_backstop` line 2695 | Semantic backstop effect | Semantic payload | safe cannot authorize; unsafe/ambiguous restrict | No emit | accepted restrict-only |
| `intent_boundary_contract.py` | `_validate_strict_deterministic_safe_subset` line 2706 | Mechanical safe subset | Strict proof only | mechanical registry only | No emit | accepted narrow mechanical path |
| `intent_boundary_contract.py` | `validate_intent_boundary_contract` line 2911 | Core validator authority | Raw message, proposal, proof, verifier, replay | all invariants; replay safe required for natural-language route | Produces contract | accepted |
| `intent_boundary_contract.py` | report/final flags lines 3157-3200 | Contract route flags | Aggregated validated intents and replay metadata | no unsafe/ambiguous/semantic restrict; governed ERP mode | No emit | accepted |

### Proposal Classifier Evidence

| File | Function / Line | Authority Decision Influenced | Input Trusted | V1-IB Gate | Can Emit/Route/Trace | Classification |
|---|---:|---|---|---|---|---|
| `intent_boundary_proposal_classifier.py` | `ROUTE_AUTHORITY_FIELDS` line 41 | Prevents authority fields in classifier output | Classifier output cleanup | forbidden authority fields popped | No emit | accepted evidence-only |
| `intent_boundary_proposal_classifier.py` | `_safe_factual_match` line 203 | Safe-shape evidence | Tokens/targets | evidence only; extra tokens marked | No emit | accepted evidence-only |
| `intent_boundary_proposal_classifier.py` | `_evidence_flags` line 232 | Unsafe/restrictive evidence | Tokens | evidence only, not route authority | No emit | accepted evidence-only |
| `intent_boundary_proposal_classifier.py` | `_clause_payload` line 314 | Clause evidence | Normalized text fragments | evidence only | No emit | accepted evidence-only |
| `intent_boundary_proposal_classifier.py` | `build_intent_boundary_proposal` line 380 | Proposal evidence | Raw message | route authority fields removed lines 486-488 | No emit | accepted evidence-only |

### Legacy / Rejected Authority Surfaces

| File | Function / Line | Authority Decision Influenced | Input Trusted | V1-IB Gate | Can Emit/Route/Trace | Classification |
|---|---:|---|---|---|---|---|
| `user_intent_boundary.py` | constants/regex/phrase lists lines 9-280 | Legacy lexical boundary | Regex/phrase/token heuristics | merged restrictively via V1-IB runtime integration | No direct emit from module | legacy restrict-only in runtime; must retire/quarantine later |
| `service.py` | legacy build line 4065 | Legacy boundary construction | Raw message | `merge_v1_ib_with_legacy_boundary` restricts only | Metadata input | accepted restrict-only but D-4 retirement target |
| `intent_boundary_structural_classifier.py` | module lines 1-120 | Rejected structural classifier scratch | Regex/token structural classifier | not referenced by runtime; only old test imports it | No runtime emit | rejected historical scratch; must not authorize |
| `tests/test_v1_ib_structural_classifier.py` | import line 22 | Rejected structural classifier test | Old scratch module | not accepted as runtime authority | Test only | rejected historical scratch; D-4 retirement target |

### Tests Exercising Runtime Authority

| File | Test Surface | Authority Evidence Covered | Classification |
|---|---|---|---|
| `tests/test_v1_ib_intent_boundary_contract_validator.py` | Validator invariants | proof/analysis/execution/replay, semantic-safe, lexical, false-safe blocks | accepted |
| `tests/test_v1_ib_intent_boundary_proposal_classifier.py` | Evidence-only classifier | no authority fields, ambiguity/residual/unsafe evidence | accepted |
| `tests/test_v1_ib_runtime_integration.py` | Runtime helper/gate integration | fail-closed runtime boundary, legacy restrict-only merge, context helper currentness | accepted |
| `tests/test_v1_ib_runtime_adversarial_prerouting.py` | Pre-routing adversarial | classifier/semantic/legacy cannot override V1-IB block | accepted |
| `tests/test_v1_ib_runtime_adversarial_final_emission.py` | Final-emission leak/veto | selected answer payloads sanitized under V1-IB block | accepted |
| `tests/test_v1_ib_runtime_final_emission_contract_veto.py` | Stale/mismatch final-emission veto | current raw/normalized hash matching required | accepted |
| `tests/test_v1_ib_service_adversarial_visible_context.py` | Service visible-context | stale/mismatch/raw-message-less/non-redaction-safe context blocks | accepted |
| `tests/test_v1_ib_service_adversarial_report_routing.py` | Service report routing | selector/artifact cannot override V1-IB block | accepted |
| `tests/test_v1_ib_service_adversarial_model_reasoning.py` | Service model reasoning | semantic-safe/prior context cannot activate reasoning after V1-IB block | accepted |
| `tests/test_v1_ib_service_adversarial_report_selector.py` | Service selector/compiled query | selector/compiled cannot override V1-IB block | accepted |
| `tests/test_v1_ib_service_adversarial_trace_redaction.py` | Service trace redaction | blocked prompts do not leak payload markers | accepted |
| `tests/test_v1_ib_service_adversarial_long_context_full_stack.py` | Long-context/full-stack | optimistic downstream stack defeated by V1-IB block | accepted |
| `tests/test_authorized_emission_contracts.py` | Authorized emission contracts | final answer authority still requires V1-IB for business output | accepted |
| `tests/test_service_control_authorized_emission_contracts.py` | Legacy authorized-emission alignment | governed business final answer requires current V1-IB authority | accepted |
| `tests/test_user_intent_boundary_prerouting_gate.py` and `tests/test_user_intent_boundary_lexical_fragility.py` | Legacy boundary behavior | legacy lexical behavior is present and tested historically | legacy/backlog; not accepted as V1-IB route authority |

## 4. Authority Surface Table

| Surface | Current Authority Source | Allowed Authority Source | Bypass Risk | Existing Evidence/Tests | Remaining Gap | Recommended Next Slice |
|---|---|---|---|---|---|---|
| Pre-routing | Merged V1-IB runtime boundary | Current validated V1-IB contract only | Frontdoor/semantic evidence is computed before pre-routing gate but should not emit | C-2, C-3-2, C-3-6 | Assert every pre-gate evidence surface remains non-emissive | D-2 |
| Visible context | Strict current context helper | Current hash-matching trace-safe V1-IB context allow | Stale/missing/raw-message-less context; local projection side paths | C-3-4, C-3-6 | Cross-lane same-contract identity assertions | D-2 |
| Report routing | Runtime normalized `report_routing_allowed` | Current validated V1-IB report allow | Selector/frontdoor candidate self-authorization | C-3-4, C-3-5, C-3-6 | Call-site map tests around frontdoor/requery/compiled lanes | D-2 |
| Model reasoning | Runtime path after pre-routing/context/report checks | Current V1-IB authority plus existing reasoning constraints | Semantic-safe or prior grounded context activating reasoning | C-3-5, C-3-6 | Same-contract propagation into reasoning trace | D-2/D-3 |
| Compiled query / governed requery | Runtime gate plus report/context authority | Current V1-IB report authority | Requery continuation from prior context or frontdoor | C-3-5, C-3-6 | Explicit stale/mismatch contract identity across requery | D-2 |
| Final emission | `authorized_emission.emit_authorized_assistant_answer` V1-IB veto | Current hash-matching trace-safe V1-IB contract | Selected answer/final authority alone | C-2-A, C-2-B, C-3-2 | Ensure all business answer types covered in D-level consistency | D-2 |
| Trace metadata | Redacted V1-IB metadata and audit payloads | Redaction-safe metadata only | Business payloads in trace/diagnostics | C-3-5, C-3-6 | Formal diagnostic contract audit | D-3 |
| Legacy intent boundary | `user_intent_boundary.py` merged restrictively | Restrict/fail closed only | Legacy lexical allow expands V1-IB | C-2/C-3 tests, merge helper | Retirement/quarantine plan | D-4 |
| Proposal classifier | `build_intent_boundary_proposal` evidence | Evidence only | Classifier output mistaken as authority | B/B-A/B-B tests, contract tests | D-level API inventory and no-authority assertions | D-2 |
| Semantic backstop | Validator restrict-only semantic status | Restrict only | Semantic-safe mistaken as allow | A/C tests, C-3-5 | Cross-lane semantic optimistic tests | D-2 |
| Selected answer payloads | Final emission subject to V1-IB veto | Never authority | Payload leaks after veto | C-2-A/C-3 tests | Broader answer-type matrix | D-2/D-3 |
| Prior context/artifacts | Context/requery lanes gated by V1-IB | Never authority | Long-context bleed-through | C-3-6 | More contract identity assertions over prior-context flows | D-2 |

## 5. Legacy Authority Audit

Legacy surfaces found:

- `qwen_chat/user_intent_boundary.py` remains present with regex/phrase/token logic. Runtime use is currently through `build_user_intent_boundary_contract(raw_msg)` in `service.py` line 4065 and through final-emission fallback rebuild in `authorized_emission.py` line 406.
- `merge_v1_ib_with_legacy_boundary` in `intent_boundary_runtime_integration.py` line 267 classifies legacy metadata as restrict-only. If legacy blocks a V1-IB allow, it can remove route flags; it does not expand V1-IB allow.
- `qwen_chat/intent_boundary_structural_classifier.py` and `tests/test_v1_ib_structural_classifier.py` remain present as rejected historical scratch. Runtime grep found no runtime import of the structural classifier. It is not accepted as authority.

Classification:

- `user_intent_boundary.py`: restrict-only / fail-closed acceptable for now, must retire or quarantine later.
- Legacy metadata in V1-IB runtime boundary: evidence/restrict-only acceptable for now.
- Old structural classifier: rejected historical scratch, must not authorize, must retire/quarantine before packaging.
- Old structural classifier test: rejected historical scratch test, must not be used as acceptance evidence.

No D-1 source fix was made.

## 6. Bypass Hypotheses For D-2

D-2 should test these concrete hypotheses:

- Stale contract reaches visible context.
- Raw-message-less context helper authorizes context reuse.
- Normalized-hash mismatch reaches visible-context emission.
- Report selector/frontdoor result runs after V1-IB block and emits.
- Compiled query runs after V1-IB block.
- Governed requery runs after V1-IB block.
- Model reasoning activates from semantic-safe output despite V1-IB block.
- Prior grounded context activates reasoning despite V1-IB block.
- Final emission accepts selected business answer without current V1-IB.
- Final emission accepts stale current-looking authority context with mismatched hash.
- Trace leaks selected rows, artifacts, rendered payloads, narratives, grounded evidence, or helper payloads after veto.
- Legacy intent logic grants route permission.
- Rejected structural classifier output is mistaken as accepted authority.
- Proposal classifier evidence is mistaken as authority.
- Semantic backstop safe result is mistaken as authority.
- NBU shadow trace or runtime diagnostics expose raw business payload on blocked turns.

## 7. D-2 Recommendation

Recommended next slice:

```text
V1-IB-D-2 authority consistency tests, tests-only
```

Likely future test files, to be proposed/approved before creation:

- `tests/test_v1_ib_d_authority_surface_consistency.py`
- `tests/test_v1_ib_d_cross_lane_contract_identity.py`
- `tests/test_v1_ib_d_trace_diagnostic_authority_consistency.py`

Recommended D-2 assertions:

- Every runtime lane uses the same current V1-IB contract hash.
- No lane can reinterpret raw text independently as route authority.
- Missing/stale/mismatched/non-redaction-safe contracts fail closed across all lanes.
- Legacy, classifier, semantic-safe, selected-answer, report-selector, compiled-query, visible-context, model-reasoning, prior-context, and trace metadata cannot authorize.
- Safe controls still pass only with current validated V1-IB authority.

D-2 should remain tests-only unless a failing test proves a real runtime blocker; any source fix should be a separate approved slice.

## 8. Verification

Report present:

```text
report_present=PASS
```

Git hygiene:

```text
git diff --check: PASS
git diff --cached --check: PASS
staged_files=0
dirty_worktree_count=133
```

Qwen enterprise guardrail:

```text
Qwen enterprise guardrail audit: PASS
```

Fake-Frappe service import and direct assistant inventory:

```text
FAKE_FRAPPE_SERVICE_IMPORT=PASS
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

Excluded/artifact scan:

```text
excluded_artifact_scan=PASS
```

D-1 is an inventory report. It does not claim V1-IB-D closure and does not start D-2 implementation.
