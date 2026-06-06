# V1-IB-A-P Replayed Raw-Message Safety Authority / Audit-Only Provenance Contract

## Scope

V1-IB-A-P is a pure contract and validator hardening slice. It updates only the intent-boundary contract validator and focused validator tests. It does not change runtime routing, visible-context behavior, final-emission behavior, model endpoints, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work.

## Rejected Authority Pattern

V1-IB-A-O still allowed a false-safe provenance chain to authorize governed ERP routing when stored proof, stored analysis, signed execution, hashes, replay flags, artifact hashes, and attestations all asserted safe.

V1-IB-A-P treats those records as audit prerequisites only. They can prove provenance integrity, but they cannot prove safety truth.

## Implemented Authority Rule

Natural-language ERP report routing now requires validator-owned replay during validation.

The replayed raw-message safety result is computed from:

- normalized raw message
- raw and normalized subject hash
- validator-owned analyzer id/version registry entry
- validator-owned replay source/version/config/artifact identity
- current clause span coverage
- current residual status
- current connector coverage status
- current pronoun/reference status
- current trace-redaction status

Stored `replay_status=verified`, stored proof status, stored analysis status, signed execution status, and verifier agreement remain provenance. They do not grant route authority.

## Replayed Safety Fields

The contract payload now records:

- `replayed_raw_message_safety_required`
- `replayed_raw_message_safety_status`
- `replayed_raw_message_safety_source`
- `replayed_raw_message_safety_version`
- `replayed_raw_message_safety_config_hash`
- `replayed_raw_message_safety_subject_hash`
- `replayed_raw_message_safety_final_decision`
- `replayed_raw_message_safety_evidence_match_status`
- `replayed_raw_message_safety_blocking_reason`

## Fail-Closed Conditions

The validator blocks routing if replay is missing, stale, conflicting, unreproducible, incomplete, unresolved, non-redaction-safe, or contradicts stored proof/analysis evidence.

The validator also blocks if replay detects a conservative unresolved second-intent shape. This is a restrictive alarm only. It never authorizes report routing.

## Tests Added

Focused tests now prove:

- false-safe proof plus false-safe analysis plus signed execution over unsafe mixed prompt fails
- stored analysis safe but replay unsafe fails
- stored `replay_status=verified` without validator recomputation fails
- signed execution without replay config/artifact fails
- proposer/verifier agreement cannot override replayed unsafe
- semantic safe cannot override replayed unsafe
- mixed factual plus pricing/action/legal/payment/manipulation/prediction prompts fail
- unresolved residual/reference conditions keep all route flags false
- duplicate/conflicting replay artifacts fail
- stale replay for different raw/normalized hash fails
- safe factual route passes only with replayed safe, complete, non-derived, trace-safe evidence
- existing proof-integrity tests continue to pass

## Verification

Local verification before remote sync:

- V1-IB contract validator tests: PASS, `91 passed`
- Python compile for touched files: PASS

Remote verification after sync:

- V1-IB contract validator tests: PASS, `91 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: PASS, clean
- Staged files: PASS, `0`

## Decision Target

`v1_ib_a_p_replayed_raw_message_safety_authority_ready_for_counterpart_qa_review`
