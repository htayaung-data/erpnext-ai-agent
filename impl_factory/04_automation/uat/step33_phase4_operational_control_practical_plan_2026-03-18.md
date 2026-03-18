# Phase 4 Operational Control Practical Plan

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: practical execution plan for Phase 4 Operational Control Layer  
Status: planning baseline after Phase 3 closure

## 1. Starting Point

Phase 3 is now closed with versioned evidence.

The project already has strong offline control assets:

1. replay suites and manual/browser golden packs
2. risk-tier inventory
3. ownership register
4. incident register template
5. weekly quality review template
6. KPI gate targets in the enterprise contract

Phase 4 does not replace those assets. Phase 4 turns them into an active operating system for the product.

## 2. Phase 4 Objective

The practical goal of Phase 4 is simple:

1. know what quality numbers matter
2. know where those numbers come from
3. know who owns each failure
4. know when to stop, fix, or escalate

This phase is about control, visibility, and accountability.

It is not a new behavior-class expansion phase.

## 3. What Phase 4 Must Deliver

Phase 4 is considered useful only if it produces five working control artifacts:

1. a KPI and SLO definition pack
2. a runtime signal and audit-field map
3. an operational incident workflow
4. a weekly operational review routine
5. a simple metrics reporting surface

The first version can be lightweight. It does not need a polished dashboard UI. It does need clear ownership and repeatable evidence.

## 4. Core KPI Set

The first Phase 4 KPI set should be taken directly from the enterprise contract and made operational.

### 4.1 Quality KPIs

1. wrong-report rate
2. first-turn success rate
3. unnecessary clarification rate
4. clarification loop rate
5. unsupported/no-data/permission envelope correctness
6. output-shape correctness
7. write-safety violation count

### 4.2 Runtime Health KPIs

1. P95 latency by class
2. retry count
3. fallback rate
4. planner clarify rate
5. runtime error-envelope rate

### 4.3 Control KPIs

1. incident open count by severity
2. incident reopen count
3. mean time to triage
4. mean time to close
5. percentage of incidents with linked regression assets

### 4.4 Release-Control KPIs

1. audit envelope completeness
2. behavior-class mandatory coverage
3. behavior-class first-run pass rate

## 5. Runtime Signal Map

Phase 4 must define exactly which runtime fields feed which KPI.

The initial signal map should use the audit envelope and contract-required fields already defined in governance:

1. behavior class
2. task class
3. selected capability/report
4. clarification reason code
5. response envelope type
6. topic/result linkage
7. latency and retry counts
8. security policy outcome

For each signal, Phase 4 must record:

1. source field or log path
2. whether it is required or optional
3. whether it is available today or needs implementation
4. which KPI depends on it

## 6. Practical Work Packages

### WP1. KPI and SLO Specification

Goal:
turn contract-level KPI statements into operational definitions.

Deliverables:

1. KPI name
2. formula
3. sample window
4. minimum sample size
5. owner
6. source of truth
7. alert threshold
8. stop/go threshold

Output:
`Phase 4 KPI Spec`

### WP2. Runtime Signal and Audit Inventory

Goal:
map every KPI to actual runtime evidence.

Deliverables:

1. audit field inventory
2. log source map
3. field completeness gaps
4. implementation gap list

Output:
`Phase 4 Runtime Signal Map`

### WP3. Incident Operations Model

Goal:
turn the Phase 3 incident template into a live operating process.

Deliverables:

1. incident severity model: `P1`, `P2`, `P3`
2. owner assignment rule
3. triage SLA
4. closure rule
5. regression-link requirement
6. escalation rule for repeat or breach incidents

Output:
`Phase 4 Incident Operations Contract`

### WP4. Weekly Operational Review

Goal:
convert the weekly quality review template into a standing management routine.

Deliverables:

1. review owner
2. review cadence
3. required participants
4. mandatory evidence pack
5. fixed review agenda
6. decision outputs: `stable`, `watch`, `at risk`

Output:
`Phase 4 Weekly Operations Review Pack`

### WP5. Metrics Reporting Surface

Goal:
make the KPI set visible every week.

Deliverables:

1. first version metrics report
2. trend table for the main KPIs
3. incident summary table
4. class-level health summary

Output:
`Phase 4 Metrics Report`

Important note:
the first reporting surface can be markdown, CSV, or JSON-driven. A polished web dashboard is optional later.

## 7. Recommended Execution Order

This is the practical order I recommend.

### Step 1. Freeze Phase 4 KPI Definitions

Do this first.

Without KPI definitions, any later dashboard or alerting work will drift.

### Step 2. Build the Runtime Signal Map

Do this second.

This tells us what is already measurable and what still needs instrumentation.

### Step 3. Formalize Incident Operations

Do this third.

Once a metric breaches, the team must know exactly what happens next.

### Step 4. Start Weekly Operations Review

Do this fourth.

Run the first review using the latest Phase 3 closure state as the baseline.

### Step 5. Publish the First Metrics Report

Do this fifth.

This can be simple, but it must be versioned and repeatable.

## 8. First Practical Deliverables

The first deliverables for Phase 4 should be:

1. `step34_phase4_kpi_slo_spec_2026-03-18.md`
2. `step35_phase4_runtime_signal_map_2026-03-18.md`
3. `step36_phase4_incident_operations_contract_2026-03-18.md`
4. `step37_phase4_weekly_operations_review_baseline_2026-03-18.md`

These four documents are enough to start Phase 4 cleanly without touching production runtime yet.

## 9. Roles and Ownership

Initial ownership can stay simple.

### Primary Owner

AI Runtime Engineering

Responsibilities:

1. KPI definition
2. incident triage
3. regression linkage
4. weekly operational review

### Secondary Participants

1. Product owner or business reviewer
2. QA or browser validation owner
3. platform/deployment owner when runtime or latency issues appear

## 10. Done Criteria for Phase 4

Phase 4 should close only when all of the following are true:

1. KPI/SLO definitions are versioned and approved
2. runtime signals are mapped to each KPI
3. missing instrumentation gaps are explicitly listed
4. incident workflow is active with owner and SLA
5. at least two weekly operational reviews have been completed
6. at least one metrics report has been published from real project data
7. stop/escalation rules are explicitly tied to operational metrics

## 11. What Phase 4 Must Not Become

Phase 4 must not drift into:

1. new behavior-class development
2. UI beautification work
3. dashboard-first work without metric definition
4. security hardening work that belongs to Phase 5
5. rollout automation work that belongs to Phase 6

## 12. Immediate Recommendation

The most practical next move is:

1. create the KPI/SLO spec
2. create the runtime signal map
3. stop and review those two docs before building anything further

That keeps Phase 4 small, controlled, and enterprise-aligned from the start.
