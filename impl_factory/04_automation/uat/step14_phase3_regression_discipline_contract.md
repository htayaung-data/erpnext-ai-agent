# Phase 3 Regression Discipline Contract

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: enterprise regression control after Phase 2 closure  
Status: active governing contract for Phase 3

## Purpose
Phase 3 exists to turn recent stabilization work into a repeatable quality system.

The goal is not to add more fixes directly. The goal is to make sure:

1. known failures do not come back
2. new behavior work cannot bypass risk controls
3. shared-runtime changes trigger the right reruns
4. replay, browser, and release evidence stay connected

## Core Principle
Every important failure must become a permanent controlled asset.

A failure is not considered closed just because:

1. one prompt now works
2. one browser run looks correct
3. one targeted replay case passes

A failure is considered closed only when:

1. the root-cause family is identified
2. the class invariant is defined
3. the fix stays inside contract boundary
4. regression coverage is added
5. reruns appropriate to impact are green

## Non-Negotiable Boundaries
1. No prompt-to-report runtime maps.
2. No case-ID hacks.
3. No keyword-driven business routing in runtime modules.
4. No skipping replay because browser looks good.
5. No skipping browser/manual checks because replay looks good.
6. No broad reruns without impact justification.
7. No new class expansion before Phase 3 controls are in place.

## What Phase 3 Must Produce
Phase 3 must leave the project with:

1. a risk-tier matrix for test assets
2. an incident taxonomy
3. a standard incident-to-regression workflow
4. rerun rules by impact surface
5. a standing browser smoke pack
6. ownership for critical failure families
7. a review cadence for quality evidence

## Risk Tier Matrix

### Tier 1
High business, safety, or compliance impact.

Examples:

1. finance-critical reads
2. receivables / payables
3. write confirmation / delete / cancel paths
4. tenant boundary or permission-sensitive behavior
5. wrong-report defects that can mislead decisions materially

Required evidence:

1. replay coverage
2. targeted module/unit coverage
3. curated browser/manual golden coverage
4. release-gate participation
5. named owner

### Tier 2
Important analytical behavior with moderate business impact.

Examples:

1. ranking
2. projection
3. transform follow-up
4. correction/rebind
5. latest-record flows
6. time series and comparisons

Required evidence:

1. replay coverage
2. variation-matrix coverage
3. targeted browser smoke
4. impact-based existing-suite reruns

### Tier 3
Low-risk convenience or display-only behavior.

Examples:

1. formatting-only transforms
2. label/presentation refinements
3. low-risk UX improvements

Required evidence:

1. focused regression
2. smoke verification when shared surfaces change

## Incident Taxonomy
Every incident must be labeled as one primary family:

1. class selection failure
2. resolver/report selection failure
3. state carryover / topic authority failure
4. transform-followup failure
5. projection/shaping failure
6. quality-gate misclassification
7. write-safety failure
8. browser/replay parity failure
9. capability metadata gap
10. ontology normalization gap

## Incident-To-Regression Workflow
When a P1 or P2 incident is found:

1. record the user-visible symptom
2. classify the incident family
3. identify the class invariant that was violated
4. identify impacted shared surfaces
5. implement the contract-safe fix
6. add permanent regression coverage
7. attach replay/browser evidence
8. record owner and closure status

## Mandatory Regression Assets Per Closed Failure
Every closed P1/P2 incident must leave behind:

1. at least one targeted unit or module-level regression
2. at least one replay case or replay-family proof
3. browser/manual evidence if the failure was user-visible
4. risk tier assignment
5. impact note listing rerun obligations

## Rerun Policy By Impact Surface

### Ontology Or Metadata Change
Rerun:

1. affected class suite in full
2. impacted read suites
3. browser smoke for the affected behavior family

### Memory / Resume / Follow-Up State Change
Rerun:

1. `multiturn_context`
2. `transform_followup`
3. affected browser smoke pack

### Resolver / Capability Selection Change
Rerun:

1. `core_read`
2. any affected class suite
3. browser smoke for report-selection-sensitive flows

### Response Shaping / Projection Change
Rerun:

1. affected class suite
2. `core_read` if shared shaping surfaces are touched
3. projection browser smoke pack

### Write Path Change
Rerun:

1. `write_safety`
2. targeted browser/manual safety pack

### Structural Refactor
Rerun:

1. the directly affected suites
2. the core smoke replay set
3. the curated browser smoke pack
4. the release gate if closure or release is being considered

## Standing Browser Smoke Pack
This pack must remain green after significant shared-runtime changes:

1. customer ranking + scale
2. supplier ranking + scale
3. product ranking + projection
4. warehouse ranking correction + scale
5. latest-record clarification flow
6. finance read parity
7. one write cancel/confirm safety path

## Ownership Model
Every Tier 1 and Tier 2 incident must have:

1. technical owner
2. class family
3. risk tier
4. opened date
5. regression asset link
6. evidence link
7. closed date

## Review Cadence

### Per Change
Before merge/acceptance:

1. confirm impact surface
2. run required reruns
3. attach evidence

### Weekly Quality Review
Review:

1. new incidents
2. reopened regressions
3. flakiest suites
4. browser/replay parity gaps
5. deferred risks

## Exit Criteria For Phase 3
Phase 3 is complete when:

1. every P1/P2 failure path from Phase 1 and Phase 2 has permanent regression assets
2. risk tiers are assigned to the important suites and manual packs
3. rerun policy is actively used, not just documented
4. browser smoke pack is formalized and owned
5. incident closure requires attached evidence

## Relationship To Future Expansion
Phase 3 is the gate before safe expansion.

After Phase 3 is operational:

1. new behavioral classes may be added under [step13_behavioral_class_development_contract.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_behavioral_class_development_contract.md)
2. but only if the regression-discipline rules in this document are followed
