# Contribution Share Asset Preparation Checklist

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: required asset-preparation checklist before runtime implementation of `contribution_share`  
Status: design-preparation checklist

## Purpose
This checklist defines what must be prepared before any runtime code is written for:

- `contribution_share`

The goal is to stop premature implementation and keep the class bounded, governed, and testable before code changes begin.

## Candidate
Primary reference:

1. [step17_first_approved_expansion_candidate_contribution_share.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step17_first_approved_expansion_candidate_contribution_share.md)

## Approval Rule
Runtime implementation may begin only when every required section below is complete.

If a required item is still open:

1. do not add runtime logic
2. do not add replay cases that assume missing semantics
3. do not call the class implementation-ready
4. keep status as `design-preparation`

## Section A: Class Definition
Required:

1. final class name confirmed
2. supported domains confirmed
3. supported entity grains confirmed
4. supported metric families confirmed
5. output modes confirmed
6. clarification rules confirmed
7. follow-up rules confirmed
8. explicit non-goals confirmed
9. default risk tier confirmed

Completion status:

- [x] complete

## Section B: Ontology Planning
Required:

1. canonical contribution/share term set defined
2. accepted percent-of-total phrases defined
3. accepted equivalent business wording defined
4. ambiguity cases documented
5. out-of-scope phrasing documented

Examples that must be explicitly handled in governed semantics:

1. `share of total`
2. `contribution share`
3. `contribution to total`
4. `percent of total`
5. `percentage of total`

Completion status:

- [x] complete

## Section C: Capability Metadata Planning
Required:

1. identify which reports/capabilities can support contribution-share computation
2. identify which metric columns are contribution-capable
3. identify which entity grains are valid for each report
4. identify aggregate-row policy where relevant
5. identify safe visible columns for first-turn outputs
6. identify any missing metadata that must be added before implementation

Planning inventory must cover at minimum:

1. customer revenue share
2. supplier purchase-amount share
3. item revenue share

Completion status:

- [x] complete

## Section D: Variation Matrix Design
Required:

Create the initial variation matrix before implementation.

Minimum variation groups:

1. base contribution ask
2. equivalent share phrasing
3. projection follow-up
4. restrictive `only` follow-up
5. top-n variant
6. scale follow-up
7. domain/grain variants

Completion status:

- [x] complete

## Section E: Replay Asset Design
Required:

1. define new manifest suite name
2. define required case-count target
3. define risk-tier split inside the suite
4. define mandatory cases
5. define first-run-only expectations

Minimum replay coverage must include:

1. customer revenue share
2. supplier purchase share
3. item sales share
4. projection follow-ups
5. top-n follow-ups
6. clarification and unsupported cases

Completion status:

- [x] complete

## Section F: Browser / Manual Golden Design
Required:

1. define curated browser/manual golden pack
2. include sales and purchasing coverage
3. define expected report/grain/metric for each
4. define what counts as failure

Completion status:

- [x] complete

## Section G: Rerun Impact Plan
Required:

Document which existing suites must be rerun once implementation begins.

Minimum expected reruns:

1. new contribution-share suite in full
2. `core_read`
3. `multiturn_context` if follow-up behavior is touched
4. `transform_followup` if transform reuse behavior is touched
5. standing browser smoke pack

Completion status:

- [x] complete

## Section H: Ownership And Risk
Required:

1. assign primary owner
2. confirm supporting owner if available
3. record risk tier
4. confirm whether any subflows should be upgraded to Tier 1 rigor

Expected rule:

1. customer and supplier contribution-share variants should be treated with Tier 1 rigor even if the broader class remains Tier 2

Completion status:

- [x] complete

## Section I: Implementation Go / No-Go Decision
Implementation is approved only when:

1. Sections A through H are complete
2. the preparation package is reviewed
3. the class remains inside contract boundary

Decision:

- [x] approved for runtime implementation
- [ ] not yet approved

## Current Recommendation
Current state for `contribution_share`:

1. candidate approved for controlled first-slice implementation
2. scope must remain limited to reviewed report families and metrics
3. deferred broader group-share variants must stay deferred
