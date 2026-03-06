# Phase 3 Execution Worklist

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: practical work sequence for Phase 3

## Objective
Turn the current stabilized runtime into a governed quality system that can support safe future expansion.

## Work Sequence

### Step 1. Build The Risk-Tier Map
Create a simple owned inventory of:

1. replay suites
2. browser/manual packs
3. critical unit/module regressions

For each asset record:

1. asset name
2. class family
3. tier (`1`, `2`, `3`)
4. owner
5. when it must be rerun

### Step 2. Create The Incident Register Template
Create one operational template with fields for:

1. incident ID
2. symptom
3. class family
4. root-cause family
5. risk tier
6. owner
7. linked regression assets
8. replay evidence
9. browser/manual evidence
10. closure date

### Step 3. Backfill Phase 1 And Phase 2 Incidents
Do not wait for new incidents.

Backfill the important already-fixed families:

1. transform-followup misrouting
2. ranking wrong-report selection
3. latest-record clarification resume drift
4. projection strict-only behavior
5. ranking correction carryover
6. finance receivable/payable disambiguation
7. browser/replay parity defects

### Step 4. Formalize The Standing Browser Smoke Pack
Freeze the curated browser smoke set used for Phase 2 closure into a named owned pack.

Record:

1. prompts
2. expected behavior
3. risk tier
4. when it must be rerun

### Step 5. Formalize Rerun Rules
Translate the rerun policy into an operational checklist:

1. ontology change -> which suites
2. resolver change -> which suites
3. memory/resume change -> which suites
4. shaping change -> which suites
5. write change -> which suites
6. structural refactor -> which suites

### Step 6. Add Governance Links To Existing Assets
Update the UAT/governance pack so:

1. Phase 2 closure report points forward to Phase 3
2. behavior-class development contract references Phase 3 controls
3. README links the new governance assets

### Step 7. Start Weekly Quality Review
Define a minimal review rhythm:

1. new incidents
2. reopened regressions
3. current green baseline
4. deferred risks
5. next approved expansion work

## Immediate Deliverables
Phase 3 should produce these first:

1. risk-tier inventory document
2. incident register template
3. standing browser smoke pack definition
4. rerun decision checklist

## Done For Initial Phase 3 Kickoff
The kickoff is complete when:

1. the governance documents exist
2. owners and tiers are recorded for the critical assets
3. at least the major Phase 1/2 incidents are backfilled into the new system
4. future work is required to use these controls
