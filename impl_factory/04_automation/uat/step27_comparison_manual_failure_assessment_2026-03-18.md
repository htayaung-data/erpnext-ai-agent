# Comparison Manual Failure Assessment

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: manual/browser execution assessment for `comparison` class after replay-green run  
Status: manual evidence review complete, closure blocked

## Purpose

This note records the first real browser/manual execution outcome for the `comparison` class after replay became green.

It exists to prevent false closure.

Replay evidence is green, but manual/browser evidence shows that the class is not yet closure-grade.

## Executive Decision

`comparison` must **not** be frozen yet.

`Phase 3` must **not** be closed yet.

Reason:

1. replay suite is green
2. impacted replay suites are green
3. manual/browser behavior is still materially incorrect for several core `comparison` scenarios

Under program principle `green means replay suites and manual golden set, not one only`, this class is still open.

## Key Conclusion

The current implementation has reached **spec-level and replay-level correctness**, but not yet **user-visible comparison behavior correctness**.

That means:

1. some requests route to the wrong visible report
2. some requests produce correct raw data but wrong presentation shape
3. some unsupported / clarification cases still answer directly instead of respecting policy

## Assessment By Manual Case

## Pack A: Territory Comparison

### MG-CMP-01
Prompt:

- `Compare Yangon and Mandalay sales last month by territory`

Observed:

- `Sales Payment Summary`
- one-column `Revenue` output with many rows

Assessment:

- `FAIL`

Reason:

1. wrong comparison grain
2. not a deterministic side-by-side territory comparison table
3. not closure-grade for `comparison`

### MG-CMP-02
Prompt:

- `Yangon vs Mandalay revenue last month`

Observed:

- `Territory-wise Sales`
- territories shown with `0.00`

Assessment:

- `FAIL`

Reason:

1. output is not reliable comparison behavior
2. visible result quality is incorrect despite replay pass

### MG-CMP-03
Prompt:

- same session as MG-CMP-01: `Show only territory and revenue`

Assessment:

- `NOT VALIDATED`

Reason:

1. base result in MG-CMP-01 was already wrong
2. projection follow-up cannot be accepted from an invalid base comparison result

### MG-CMP-04
Prompt:

- same session as MG-CMP-01: `Show in Million`

Observed:

- scaling applied to a wrong/non-comparison-shaped result

Assessment:

- `NOT VALIDATED`

Reason:

1. scaling behavior cannot be counted as pass when the base comparison result is wrong

## Pack B: Customer / Supplier / Item Comparison

### MG-CMP-05
Prompt:

- `Compare Shwe Li Road Mobile Wholesale and Latha Mobile Wholesale revenue last month`

Observed:

- `Sales Person-wise Transaction Summary`

Assessment:

- `FAIL`

Reason:

1. wrong visible report for customer comparison
2. report grain is transaction/detail-like, not comparison-grade summary output

### MG-CMP-06
Prompt:

- `Compare Sunflower Accessories Co. and Golden Dragon Trading Co. Ltd. purchase amount last month`

Observed:

- `Supplier Ledger Summary`
- two suppliers and purchase amounts shown correctly

Assessment:

- `PARTIAL FAIL`

Reason:

1. raw business data appears correct
2. presentation is not comparison-grade
3. expected enterprise behavior is explicit comparison output, or at minimum comparison-shaped presentation

Conclusion:

- treat this as `not yet pass`

### MG-CMP-07
Prompt:

- `Compare SPH-SAM-A15-6/128 and SPH-XMI-RN13-8/256 sales last month`

Observed:

- `Item-wise Sales Register`
- two items with sales values shown

Assessment:

- `PARTIAL`

Reason:

1. visible data appears directionally correct
2. presentation may still be plain filtered summary rather than explicit comparison shape

Conclusion:

- acceptable as promising evidence
- not enough by itself to declare closure

## Pack C: Monthly / MoM

### MG-CMP-08
Prompt:

- `Compare Yangon revenue in March 2026 vs February 2026`

Observed:

- `Sales Person-wise Transaction Summary`

Assessment:

- `FAIL`

Reason:

1. wrong report
2. not a month-vs-month comparison result

### MG-CMP-09
Prompt:

- `Show Yangon revenue month over month for March 2026`

Observed:

- `Item-wise Sales Register`
- long numeric list, not bounded MoM comparison output

Assessment:

- `FAIL`

Reason:

1. wrong report
2. wrong output shape
3. missing explicit month-over-month comparison semantics

## Pack D: Correction / Clarification / Unsupported

### MG-CMP-10
Prompt:

- same session as MG-CMP-01: `Actually compare Yangon and Bago instead`

Assessment:

- `NOT YET EVIDENCED`

Reason:

1. no valid confirmed browser evidence recorded yet

### MG-CMP-11
Prompt:

- `Compare Yangon and Mandalay`

Observed:

- direct result returned instead of blocker clarification

Assessment:

- `FAIL`

Reason:

1. metric and/or comparison grain is missing
2. expected behavior is bounded clarification, not direct execution

### MG-CMP-12
Prompt:

- `Compare Yangon revenue week over week`

Assessment:

- `NOT YET EVIDENCED IN THIS NOTE`

Reason:

1. not included in the pasted manual evidence set here
2. still required before closure

### MG-CMP-13
Prompt:

- `Compare Yangon revenue quarter over quarter`

Observed:

- direct result returned instead of safe unsupported

Assessment:

- `FAIL`

Reason:

1. quarterly comparison is explicitly out of scope for approved first slice
2. expected behavior is safe unsupported response

## Summary Table

### Clear Failures

1. `MG-CMP-01`
2. `MG-CMP-02`
3. `MG-CMP-05`
4. `MG-CMP-08`
5. `MG-CMP-09`
6. `MG-CMP-11`
7. `MG-CMP-13`

### Partial / Not Closure-Grade Yet

1. `MG-CMP-06`
2. `MG-CMP-07`

### Not Yet Validated From Clean Base

1. `MG-CMP-03`
2. `MG-CMP-04`
3. `MG-CMP-10`
4. `MG-CMP-12`

## Why Replay Green Was Not Enough

Current replay assertions for `comparison` prove:

1. spec normalization is mostly correct
2. behavior class is mostly correct
3. output shape is minimally acceptable

But current replay does **not fully prove**:

1. the visible report is the right business report for manual/browser use
2. the visible presentation is comparison-grade
3. unsupported and clarification behavior remain correct under broader browser phrasing/session conditions

This is exactly why manual golden execution remains mandatory.

## Enterprise Interpretation

This is not a failure of the contract process.

This is the contract process working correctly:

1. replay found structural/runtime correctness improvements
2. manual/browser testing exposed remaining user-visible defects
3. closure is therefore blocked until manual behavior matches approved class intent

## Immediate Next Step

Do **not** freeze the comparison slice yet.

Do this next:

1. use this note as the authoritative blocker record
2. design the smallest remediation order for manual-failing scenarios only
3. strengthen comparison acceptance so replay better reflects visible business behavior
4. only then resume runtime fixes

## Guardrail

No new broad comparison expansion should be added during remediation.

Only fix:

1. wrong visible report selection
2. non-comparison-grade comparison presentation
3. missing clarification / unsupported enforcement for approved out-of-scope cases
