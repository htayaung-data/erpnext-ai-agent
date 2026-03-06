# Threshold Exception List Asset Preparation Checklist

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: required asset-preparation checklist before runtime implementation of the first approved expansion candidate  
Status: design-preparation checklist, implementation not yet approved

## Purpose
This checklist defines what must be prepared before any runtime code is written for the first approved expansion candidate:

- `threshold_exception_list`

The goal is to stop premature implementation and make sure the class is designed, governed, and testable before code changes begin.

## Candidate
Primary reference:

1. [step15_first_approved_expansion_candidate_threshold_exception_list.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_first_approved_expansion_candidate_threshold_exception_list.md)

## Approval Rule
Runtime implementation may begin only when every item in the required sections below is complete.

If a required item is still open:

1. do not add runtime logic
2. do not add replay cases that assume missing semantics
3. do not call the class “in development”
4. keep status as `design-preparation`

## Section A: Class Definition
Required:

1. final class name confirmed
2. supported domains confirmed
3. supported entity grains confirmed
4. supported metric families confirmed
5. supported comparators confirmed
6. output modes confirmed
7. clarification rules confirmed
8. follow-up rules confirmed
9. explicit non-goals confirmed
10. default risk tier confirmed

Completion status:

- [ ] complete

## Section B: Ontology Planning
Required:

1. canonical comparator set defined
2. accepted threshold phrases defined
3. accepted exception phrases defined
4. comparator-to-canonical mapping defined
5. threshold-value extraction rules defined
6. ambiguity cases documented
7. out-of-scope phrasing documented

Examples that must be explicitly handled in governed semantics:

1. `above`
2. `below`
3. `greater than`
4. `less than`
5. `over`
6. `under`
7. `more than`
8. `fewer than`
9. `overdue`
10. `below minimum stock`

Completion status:

- [ ] complete

## Section C: Capability Metadata Planning
Required:

1. identify which reports/capabilities can support exception filtering
2. identify which metric columns can be threshold-filtered
3. identify which entity grains are valid for each report
4. identify status columns needed for overdue / exception flows
5. identify which reports support detail list vs summary list
6. identify aggregate-row policy where relevant
7. identify any missing metadata that must be added before implementation

Planning inventory should cover at minimum:

1. customer outstanding paths
2. supplier outstanding paths
3. invoice amount / overdue paths
4. stock balance and stock quantity paths
5. warehouse-related exception paths

Completion status:

- [ ] complete

## Section D: Variation Matrix Design
Required:

Create the initial variation matrix before implementation.

Minimum variation groups:

1. base threshold ask
2. equivalent comparator phrasing
3. threshold value variation
4. projection follow-up
5. restrictive `only` follow-up
6. top-n follow-up where relevant
7. domain/grain variants

Minimum example rows to define:

1. customer + outstanding amount + above threshold
2. supplier + outstanding amount + above threshold
3. invoice + overdue / grand total + above threshold
4. item + stock below threshold
5. warehouse + stock balance below threshold

Completion status:

- [ ] complete

## Section E: Replay Asset Design
Required:

1. define new manifest suite name
2. define required case count target
3. define risk-tier split inside the suite
4. define mandatory cases
5. define first-run-only expectations

Minimum replay coverage should include:

1. finance exception cases
2. inventory exception cases
3. comparator variants
4. threshold parsing variants
5. projection follow-ups

Completion status:

- [ ] complete

## Section F: Browser / Manual Golden Design
Required:

1. define curated browser/manual golden pack
2. include both finance and inventory exception examples
3. define expected report/grain/metric for each
4. define what counts as failure

Minimum manual golden candidates:

1. `Show customers with outstanding amount above 10000000`
2. `Show suppliers with outstanding amount above 20000000`
3. `Show overdue sales invoices above 5000000`
4. `Show items with stock below 20 in Main warehouse`
5. `Show warehouses with stock balance below 50000000`

Completion status:

- [ ] complete

## Section G: Rerun Impact Plan
Required:

Document which existing suites must be rerun once implementation begins.

Minimum expected reruns:

1. new exception-list suite in full
2. `core_read`
3. `multiturn_context` if follow-up behavior is touched
4. standing browser smoke pack
5. release gate if milestone closure or release is being prepared

Completion status:

- [ ] complete

## Section H: Ownership And Risk
Required:

1. assign primary owner
2. confirm supporting owner if available
3. record risk tier
4. confirm whether any sub-flows should be upgraded to Tier 1

Expected rule:

1. finance exception variants should be treated with Tier 1 rigor even if the broader class is Tier 2

Completion status:

- [ ] complete

## Section I: Implementation Go / No-Go Decision
Implementation is approved only when:

1. Sections A through H are complete
2. the preparation package is reviewed
3. the class remains inside contract boundary

Decision:

- [ ] approved for runtime implementation
- [ ] not yet approved

## Current Recommendation
Current state for `threshold_exception_list`:

1. candidate approved for design
2. not approved for runtime implementation yet
3. next correct work is asset preparation, not coding
