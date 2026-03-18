# Comparison Asset Preparation Checklist

Date: 2026-03-07  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: required asset-preparation checklist before runtime implementation of `comparison`  
Status: design-preparation checklist

## Purpose
This checklist defines what must be prepared before any runtime code is written for:

- `comparison`

The goal is to prevent premature implementation and keep expansion bounded and contract-safe.

## Candidate

1. [step23_first_approved_expansion_candidate_comparison.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_first_approved_expansion_candidate_comparison.md)

## Approval Rule
Runtime implementation may begin only when all required sections are complete.

If any required item is open:

1. do not add runtime logic
2. do not widen replay assumptions
3. keep status as `design-preparation`

## Section A: Class Definition
Required:

1. class name confirmed
2. in-scope domains confirmed
3. in-scope grains confirmed
4. metric families confirmed
5. clarification rules confirmed
6. unsupported rules confirmed
7. follow-up rules confirmed
8. explicit non-goals confirmed
9. risk tier confirmed

Completion status:

- [x] complete

## Section B: Ontology Planning
Required:

1. canonical comparison intent set defined
2. comparison phrasing aliases defined
3. ambiguity/clarification triggers documented
4. out-of-scope weekly/quarterly/YoY wording documented

Completion status:

- [x] complete

## Section C: Capability Metadata Planning
Required:

1. comparison-capable report families identified
2. metric-to-grain compatibility declared
3. entity filter semantics declared
4. aggregate-row policy declared
5. safe output columns declared

Completion status:

- [x] complete

## Section D: Variation Matrix Design
Required:

1. base ask variants
2. equivalent phrasing variants
3. monthly period-vs-period variants
4. bounded MoM variants
5. projection follow-up variants
6. restrictive `only` follow-ups
7. correction follow-ups
8. unsupported weekly/quarterly/YoY cases

Completion status:

- [x] complete

## Section E: Replay Asset Design
Required:

1. suite design and case groups
2. mandatory first-slice comparison cases
3. clarification/unsupported coverage
4. first-run-only expectations
5. monthly boundary and MoM boundary coverage

Completion status:

- [x] complete

## Section F: Browser / Manual Golden Design
Required:

1. curated manual pack with pass/fail invariants
2. same-period comparison cases
3. monthly period-vs-period cases
4. bounded MoM cases
5. follow-up cases
6. unsupported weekly/quarterly case

Completion status:

- [x] complete

## Section G: Rerun Impact Plan
Required:

1. required impacted suites listed
2. shared-surface rerun rule mapped
3. closure evidence obligations listed

Completion status:

- [x] complete

## Section H: Ownership And Risk
Required:

1. primary owner identified
2. risk tier confirmed
3. tier-escalation rule for finance-adjacent cases documented

Completion status:

- [x] complete

## Section I: Implementation Go/No-Go
Implementation starts only if Sections A through H are complete and approval review is accepted.

Decision:

- [x] approved for controlled runtime implementation planning
- [ ] not approved

## Current Recommendation

1. planning package is complete
2. first slice now includes same-period comparison, monthly period-vs-period, and bounded MoM only
3. weekly/quarterly/YoY and advisory behaviors remain explicitly deferred
