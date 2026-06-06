# V1-IB-B-0 Deterministic Classifier Restart Plan From Accepted A-Q Foundation

## Scope

V1-IB-B-0 is a report-only restart plan. It does not implement classifier code, runtime routing, visible-context wiring, final-emission changes, model endpoint changes, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work.

QA_Risk accepted V1-IB-A-Q as the contract/validator foundation closure checkpoint only. V1-IB-A-Q does not accept any existing V1-IB-B artifacts.

## Accepted A-Q Authority Model

The accepted V1-IB-A-Q authority model is:

- Proposer/model output cannot authorize routing.
- Verifier output cannot authorize routing.
- Proof, analysis, execution, registry, hash, attestation, artifact, and stored replay records cannot authorize routing by themselves.
- Stored `replay_status=verified` cannot authorize routing.
- Semantic safe output cannot authorize routing.
- Lexical, regex, keyword, synonym, phrase, and punctuation evidence cannot authorize routing.
- Punctuation is not intent. It may restrict when replay cannot prove safety, but it cannot authorize or block a proven positive safe factual lookup by itself.
- Governed ERP routing requires positive validator-owned safe factual replay plus all accepted contract/validator invariants.
- Unknown, ambiguous, unsafe, mixed, unresolved, stale, conflicting, non-redaction-safe, or unproven natural-language ERP intent fails closed.
- The safe factual route is a narrow V1 subset only. It is not broad natural-language ERP understanding.

## What V1-IB-B May Do

V1-IB-B may build a deterministic classifier/proposal generator as a pure evidence layer.

Allowed responsibilities:

- Normalize raw message text for proposal construction.
- Produce structured clause candidates.
- Produce ERP target candidates.
- Produce visible-context reference candidates.
- Produce factual/advice/action/mixed/ambiguous evidence fields.
- Produce confidence/status/completeness fields.
- Feed the accepted `IntentBoundaryContract` validator.
- Emit proposals that may be accepted, rejected, or restricted by the validator.
- Support test fixtures that prove the classifier has no route authority.

V1-IB-B output is proposal evidence only. It must never be treated as authority.

## What V1-IB-B Must Not Do

V1-IB-B must not:

- Grant `report_routing_allowed=true`.
- Grant `context_reuse_allowed=true`.
- Grant `model_reasoning_allowed=true`.
- Grant `final_emission_allowed=true`.
- Select `required_answer_mode=governed_erp_answer`.
- Make final report-routing decisions.
- Make visible-context activation decisions.
- Make final-emission decisions.
- Use broad lexical, synonym, regex, keyword, phrase, or punctuation matching as route authority.
- Treat absence of an alarm as safety.
- Override validator-owned replay.
- Override semantic unsafe/ambiguous restriction.
- Reintroduce the rejected deterministic structural classifier authority path.

## Existing V1-IB-B Artifact Audit

Existing dirty worktree V1-IB-B artifacts are unaccepted/rejected and must not be reused as accepted design:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py`

Restart recommendation:

- Treat the old B reports as rejected historical context only.
- Do not package old B/B-A/B-B reports as accepted deliverables.
- Delete or supersede `intent_boundary_structural_classifier.py` in the future implementation slice unless a line-by-line audit proves reusable pure extraction helpers with no authority semantics.
- Rewrite `test_v1_ib_structural_classifier.py` from the A-Q authority model. Do not preserve tests that assert classifier-created route authority.
- Any retained helper must be renamed or documented as proposal evidence only.

## Proposed V1-IB-B Proper File Boundary

Exact files for a future V1-IB-B implementation should be separately approved before editing.

Proposed allowed files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_proposal_classifier.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_proposal_classifier.py`
- one V1-IB-B governance report

Alternative if Owner/QA wants to reuse old names:

- Replace `intent_boundary_structural_classifier.py` wholesale and mark old content superseded.
- Replace `test_v1_ib_structural_classifier.py` wholesale and mark old test assumptions superseded.

In either path, the classifier module must not export a route-authorizing API. It should export proposal-building only.

## Classifier Output Contract

The classifier should output a structured proposal payload containing evidence fields such as:

- `raw_message_hash`
- `normalized_message_hash`
- `normalized_message`
- `proposal_source`
- `proposal_run_id`
- `proposal_status`
- `proposal_confidence`
- `clause_candidates`
- `erp_target_candidates`
- `visible_context_reference_candidates`
- `factual_lookup_evidence`
- `advice_intent_evidence`
- `decision_intent_evidence`
- `business_action_evidence`
- `policy_boundary_evidence`
- `mixed_intent_evidence`
- `ambiguous_intent_evidence`
- `residual_text_evidence`
- `connector_evidence`
- `pronoun_reference_evidence`
- `trace_redaction_status`

The output must not contain authority fields that grant routing. Forbidden classifier-owned fields include:

- `report_routing_allowed`
- `context_reuse_allowed`
- `model_reasoning_allowed`
- `final_emission_allowed`
- `required_answer_mode=governed_erp_answer`
- `authority_decision=allow_report`
- `validator_owned_safe_route_authority_status=validator_safe_route_proven`

If the validator needs those fields, it must compute them after validating the proposal and replay evidence.

## Fail-Closed Behavior

Classifier output must fail closed by design:

- Unknown classifier result produces non-authoritative proposal evidence only.
- Ambiguous classifier result produces non-authoritative proposal evidence only.
- Low-confidence classifier result produces non-authoritative proposal evidence only.
- Partial classifier result produces non-authoritative proposal evidence only.
- Contradictory classifier result produces non-authoritative proposal evidence only.
- Omitted clauses or unresolved residual text must be visible to the validator and must not be hidden.
- The validator remains the sole authority for all route flags.

## Required V1-IB-B Test Families

Future V1-IB-B tests must prove:

- Safe factual governed subset produces proposal evidence that the accepted validator may approve only through positive validator-owned replay.
- Unsafe decision/advice/action/legal/manipulation/prediction prompts produce non-authoritative evidence and never route by classifier output.
- Mixed factual plus unsafe prompts keep unsafe/mixed evidence visible and cannot route by classifier output.
- Ambiguous ERP text remains non-authoritative and fail-closed unless the validator independently proves safe.
- Visible-context references are proposal evidence only and cannot activate context by classifier output.
- Proposer omission attempts are represented as residual or incomplete coverage and fail validator checks.
- Classifier output never decides route flags.
- Semantic safe output cannot compensate for classifier uncertainty.
- Lexical, regex, synonym, keyword, phrase, punctuation, or no-alarm logic never grants authority.

Minimum regression families:

- Safe factual governed subset:
  - item sales
  - item price
  - supplier payable status
  - customer outstanding balance
  - invoice details
- Unsafe single-clause prompts:
  - pricing/advice
  - legal advice
  - report hiding/manipulation
  - prediction/forecast
  - write/mutation/workflow
- Mixed prompts:
  - factual lookup plus pricing advice
  - factual lookup plus legal/action request
  - factual lookup plus report hiding/manipulation
- Ambiguous prompts:
  - vague ERP overview
  - `Tell me about EC7H-ITEM-A`
  - broad `Is this okay/fine?`
- Visible-context references:
  - explicit read-only follow-up as proposal evidence
  - unsafe this/that follow-up as blocked/non-authoritative evidence

## Dirty Worktree / Packaging Status

Current dirty state is not package-ready.

Remote dirty count at the start of this restart-plan slice: `87`.
Remote dirty count after syncing this report: `88`.

Dirty state includes:

- accepted/unaccepted V1-IB-A reports and contract validator files
- unaccepted/rejected V1-IB-B artifacts
- prior V1-R reports and intent-boundary files
- deferred EC-10-G report
- modified runtime/source/test files from prior slices

No staging, commit, or push is allowed in V1-IB-B-0.

## Verification

Remote verification after report sync:

- Report present: PASS
- Diff/check: PASS
- Excluded/artifact scan: PASS, clean
- Staged files: PASS, `0`

## Decision Target

`v1_ib_b_0_deterministic_classifier_restart_plan_ready_for_counterpart_qa_review`
