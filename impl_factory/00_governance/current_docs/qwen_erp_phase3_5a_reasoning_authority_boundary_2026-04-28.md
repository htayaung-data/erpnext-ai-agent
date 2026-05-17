# Qwen ERP Phase 3.5A Reasoning Authority Boundary

Status: in progress
Date: 2026-04-28
Scope: governed boundary between evidence explanation, driver analysis, recommendation, prediction, scoring, and approval decisions.

## Purpose

Phase 3.5A starts the broader complex-business-question chapter after Phase 3.4F Customer Risk UAT guardrails.

The goal is not to add a single fix for customer risk. The goal is to make the assistant respect the authority already declared in governed metadata:

1. evidence explanation may use the current governed artifac
2. recommendation or decision requests must be explicitly allowed by metadata and policy
3. prediction, hidden scoring, unapproved severity labels, and approval decisions must fail closed unless a governed artifact authorizes them
4. fallback should remain business-natural and explain what evidence is available

## Existing Backbone Reused

The project already had a mature Phase 6 reasoning stack:

1. `reasoning_activation.py`
2. `semantic_reasoning_activation.py`
3. `reasoning_execution.py`
4. `lanes/reasoning_lane.py`
5. `ERPBusinessReasoningActivationContract`
6. `ERPBusinessReasoningContract`

This slice reuses that backbone. It does not create a second reasoning lane.

## Implemented Slice

Added `business_reasoning_policy.py` as a shared authority-policy helper.

The helper reads governed composite-family metadata, especially:

1. `blocked_variations`
2. `blocked_variation_labels`
3. `blocked_variation_aliases`

For the current Customer Risk As-Of family, metadata now explicitly blocks:

1. predictive default probability
2. collection recommendation
3. credit-limit approval decision
4. unapproved overdue severity label
5. hidden weighted risk score

## Runtime Behavior

For current-artifact follow-ups such as:

1. `who should we collect from first?`
2. `will the first customer default next month?`
3. `give me the risk score`

the assistant now gives a deterministic governed boundary rather than fabricating a recommendation, prediction, or score.

Example behavior:

1. It can show the rank and governed evidence metrics from the current artifact.
2. It clearly says the artifact does not authorize a collection recommendation or prediction.
3. It guides the user to use the ranking as evidence or define an approved policy artifact before requesting a decision.

## Integration Points

Integrated with:

1. `composite_evidence_support.py`
2. `reasoning_activation.py`
3. `reasoning_execution.py`

The same policy payload is attached to the reasoning activation grounding summary so the reasoning lane can fail closed before runtime generation.

## Enterprise Grade Notes

This is contract and metadata driven:

1. no customer-name-specific logic
2. no rank-specific hardcoding
3. no browser-output-shaped patch
4. no one-off prompt keyword rescue inside `service.py`
5. no parallel reasoning subsystem

Natural language aliases exist in metadata so future families can add their own blocked variation policy without changing orchestration code.

## Verification Targe

Focused tests should prove:

1. collection recommendation requests are bounded by metadata
2. prediction requests are bounded by metadata
3. current evidence explanations still work
4. deterministic rendered payloads skip LLM drif
5. reasoning execution blocks forbidden business variations before runtime

## Next Step

After server verification and live UAT, Phase 3.5B should expand the same authority model to driver analysis:

1. distinguish direct evidence explanation from multi-factor driver analysis
2. identify when current artifacts are sufficien
3. require governed requery or composite artifact when driver support is missing
