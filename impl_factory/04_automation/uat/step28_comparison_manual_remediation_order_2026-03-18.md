# Comparison Manual Remediation Order

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: smallest safe remediation order after manual/browser comparison failures  
Status: planning only, no runtime edits in this step

## Purpose

This note defines the **smallest remediation order** for the `comparison` class after:

1. replay became green
2. impacted suites stayed green
3. manual/browser execution exposed real user-visible failures

The goal is to fix only the closure blockers, in the safest order, without widening the class or re-entering keyword-driven behavior.

## Non-Negotiable Rule

Do **not** attempt a broad rewrite now.

Do **not** add new comparison scenarios now.

Only remediate what manual evidence proved is still broken.

## Manual Failure Clusters

The manual failures fall into three clusters:

### Cluster A: Wrong Visible Report Selection

Examples:

1. `Compare Shwe Li Road Mobile Wholesale and Latha Mobile Wholesale revenue last month`
   - returned `Sales Person-wise Transaction Summary`
2. `Compare Yangon revenue in March 2026 vs February 2026`
   - returned `Sales Person-wise Transaction Summary`
3. `Show Yangon revenue month over month for March 2026`
   - returned `Item-wise Sales Register`

Meaning:

1. spec normalization may be acceptable
2. but visible report selection is not stable enough for real browser use

### Cluster B: Correct Data, Wrong Comparison Presentation

Examples:

1. supplier comparison
2. item comparison
3. some territory outputs

Meaning:

1. result may contain the right entities and values
2. but output is still plain filtered summary, not comparison-grade presentation
3. same-period comparison must be side-by-side, with compared entities as columns

### Cluster C: Missing Clarification / Unsupported Enforcement

Examples:

1. `Compare Yangon and Mandalay`
   - should clarify, but executed directly
2. `Compare Yangon revenue quarter over quarter`
   - should safely reject, but executed directly

Meaning:

1. browser/session path is not consistently honoring the approved class boundary

## Smallest Safe Remediation Order

## Step 2A: Strengthen Acceptance First

Before more runtime fixes, tighten what must count as pass.

Reason:

1. replay is currently allowing comparison cases to pass when manual/browser behavior is still wrong
2. if we do runtime edits first without tightening acceptance, we risk another false green

What to strengthen:

1. comparison replay should validate visible business behavior more strongly for:
   - correct report family or report title where required
   - comparison-grade output shape
   - clarification / unsupported policy outcome
2. manual pack remains authoritative and must still be rerun

Boundary:

1. no tactical case-ID hacks in runtime
2. harness changes must be behavior-class driven or manifest-driven

## Step 2B: Fix Clarification / Unsupported Enforcement

Fix this before visible report refinement.

Reason:

1. these are boundary violations
2. they are lower-complexity than presentation work
3. if class boundaries are not enforced, all later report/presentation fixes are unstable

Target failures:

1. `MG-CMP-11`
2. `MG-CMP-13`
3. confirm `MG-CMP-12`

Expected result:

1. missing-metric / missing-grain prompts clarify deterministically
2. quarterly / weekly comparisons return approved unsupported behavior

## Step 2C: Fix Wrong Visible Report Selection

Fix report selection next.

Reason:

1. presentation shaping is pointless if the wrong report is selected
2. manual failures in monthly/MoM and customer comparison are primarily wrong-report failures

Target failures:

1. `MG-CMP-01`
2. `MG-CMP-02`
3. `MG-CMP-05`
4. `MG-CMP-08`
5. `MG-CMP-09`

Expected result:

1. territory comparison lands on territory-capable comparison output
2. customer comparison lands on customer-capable comparison output
3. monthly / MoM prompts land on period-comparison-capable output

Boundary:

1. no prompt-to-report hardcoding
2. solve through contract/capability/resolver/execution policy only

## Step 2D: Fix Comparison-Grade Presentation

Only after the right report path is stable.

Reason:

1. data correctness is not enough
2. enterprise comparison output must look like comparison, not just “two filtered rows”

Target failures:

1. `MG-CMP-06`
2. `MG-CMP-07`
3. any surviving territory comparison outputs that still render as plain summaries

Expected result:

1. output clearly communicates comparison semantics
2. same-period comparison uses side-by-side layout with compared entities as columns
3. follow-up projection/scaling remains stable from that comparison result

Boundary:

1. do not redesign the whole response system
2. only shape comparison outputs in the approved first slice

## Step 2E: Re-validate Follow-Ups From Valid Base Results

Only once the base comparison result is correct.

Target manual cases:

1. `MG-CMP-03`
2. `MG-CMP-04`
3. `MG-CMP-10`

Reason:

1. these depend on a correct base comparison result
2. earlier attempts are not valid evidence if the base result was wrong

## Concrete Remediation Sequence

The exact order should be:

1. strengthen comparison acceptance criteria
2. fix clarification / unsupported enforcement
3. rerun targeted comparison replay for the affected blocker cases
4. fix wrong visible report selection
5. rerun targeted comparison replay for report-selection cases
6. fix comparison-grade presentation
7. rerun targeted replay again
8. rerun manual comparison pack from clean sessions
9. only if manual pack turns green, rerun impacted suites if the fix touched shared routing/shaping layers

## What Not To Do

Do not do these:

1. do not widen comparison to weekly / quarterly / advisory
2. do not try to solve all human-language phrasing variants now
3. do not add direct phrase-to-report mapping
4. do not change unrelated classes while fixing comparison
5. do not freeze comparison based on replay alone

## Definition Of Closure Readiness After Remediation

Comparison can be frozen only when all are true:

1. `comparison_class` replay is green
2. comparison manual pack is green
3. clarification and unsupported boundaries are confirmed in browser
4. comparison output is comparison-grade, not merely filtered-summary-grade
5. impacted suites remain green if shared layers changed

## Immediate Next Step

The next implementation step should be:

1. **tighten comparison acceptance criteria**

Only after that should we touch runtime again.
