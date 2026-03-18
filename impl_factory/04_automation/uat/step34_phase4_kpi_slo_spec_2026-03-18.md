# Phase 4 KPI and SLO Specification

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: operational KPI/SLO definitions for Phase 4  
Status: first approved KPI baseline after Phase 3 closure

## 1. Purpose

This document converts the enterprise contract gates into operational metrics.

The goal is to answer five practical questions every week:

1. is quality stable
2. is runtime behavior degrading
3. are users seeing wrong or unsafe outcomes
4. are follow-up chains still reliable
5. do we need to stop, fix, or escalate

This is a control document, not a runtime artifact.

## 2. Measurement Model

Phase 4 should track each KPI in two ways:

1. operational trend window  
   Use for weekly review and early warning.
2. promotion or release gate window  
   Use for formal go/no-go decisions.

Unless otherwise noted:

1. operational trend window = trailing 7 days
2. secondary trend view = trailing 28 days
3. release gate window = latest approved replay/manual evidence pack plus required minimum sample size from contract

## 3. KPI Ownership

Primary owner for all KPIs in this first version:

`AI Runtime Engineering`

Secondary support:

1. browser/manual validation owner
2. product/business reviewer
3. platform/deployment owner for latency or availability issues

## 3A. Threshold Source Classification

To avoid mixing contract gates with new operational controls, this document uses two threshold classes:

### Contract-Gated KPIs

These are already required by the enterprise contract:

1. wrong-report rate
2. follow-up accuracy
3. unnecessary clarification rate
4. clarification loop rate
5. output-shape correctness
6. unsupported/no-data/permission envelope correctness
7. write-safety violations
8. audit envelope completeness
9. behavior-class mandatory coverage
10. behavior-class first-run pass rate
11. P95 latency once class-specific SLA is formally approved

### Phase 4 Operational Control KPIs

These are useful operational controls, but they are not promotion blockers unless later versioned into the contract:

1. first-turn success rate
2. fallback rate
3. incident reopen rate
4. incident closure discipline

## 4. KPI Definitions

### KPI-01 Wrong-Report Rate

Purpose:
measure how often the assistant returns the wrong report or wrong business answer for a clear supported ask.

Formula:

`wrong-report rate = wrong-report turns / eligible supported read turns`

Eligible turns:

1. read turns only
2. user intent is supported
3. prompt is sufficiently specific to avoid valid blocker clarification

Operational target:

`<= 5%`

Promotion gate:

`<= 5%` first-run, `n >= 300`

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. replay evidence for gated packs
2. manual browser pack for standing critical flows
3. incident register for live defects

Alert threshold:

`> 4%` in trailing 7 days

Stop/escalate threshold:

`> 5%` in qualified gate window  
or  
`> 6%` in trailing 7 days with two or more confirmed incidents

### KPI-02 First-Turn Success Rate

Purpose:
measure how often the assistant solves the ask correctly on the first assistant response without unnecessary repair.

Formula:

`first-turn success rate = successful first responses / eligible first turns`

Eligible turns:

1. supported read requests
2. supported write safety checks where the correct outcome is a safe block or governed confirmation

Operational target:

`>= 95%`

Promotion gate linkage:

covered through mandatory-suite first-run pass and class-level first-run pass targets

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. replay first-run results
2. browser/manual standing pack

Alert threshold:

`< 96%` trailing 7 days

Stop/escalate threshold:

`< 95%` on reviewed operational window  
or  
mandatory suite below contract threshold

Threshold source:

`Phase 4 operational control KPI`

### KPI-03 Follow-Up Accuracy

Purpose:
measure whether multi-turn follow-up chains remain context-correct and contamination-free.

Formula:

`follow-up accuracy = correct follow-up chains / total validated follow-up chains`

Required tracked segments:

1. 3-turn chains
2. 4-turn chains

Operational target:

1. 3-turn `>= 95%`
2. 4-turn `>= 90%`

Promotion gate:

1. 3-turn `>= 95%`
2. 4-turn `>= 90%`
3. `>= 150` validated chains

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. multiturn replay packs
2. standing browser follow-up pack
3. incident evidence for contamination failures

Alert threshold:

1. 3-turn `< 96%`
2. 4-turn `< 92%`

Stop/escalate threshold:

1. 3-turn `< 95%`
2. 4-turn `< 90%`

### KPI-04 Unnecessary Clarification Rate

Purpose:
measure how often the assistant asks a blocker clarification when the user already provided enough information.

Formula:

`unnecessary clarification rate = unnecessary clarification turns / eligible supported turns`

Operational target:

`<= 5%`

Promotion gate:

`<= 5%`

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. replay classification
2. browser/manual evidence
3. incident review when a clarification is judged avoidable

Alert threshold:

`> 4%`

Stop/escalate threshold:

`> 5%`

### KPI-05 Clarification Loop Rate

Purpose:
measure how often the assistant gets stuck in repeated clarification instead of progressing or failing safely.

Formula:

`clarification loop rate = looped clarification chains / clarification chains`

Loop definition:

two or more consecutive clarification turns without meaningful progress or safe terminal outcome

Operational target:

`< 1%`

Promotion gate:

`< 1%`

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. multiturn replay
2. browser/manual follow-up packs
3. incident review

Alert threshold:

`>= 0.5%`

Stop/escalate threshold:

`>= 1%`

### KPI-06 Output-Shape Correctness

Purpose:
measure whether returned tables, projections, envelopes, and numeric formatting follow the approved output contract.

Formula:

`output-shape correctness = compliant outputs / validated outputs`

Operational target:

`100%` on mandatory reviewed set

Promotion gate:

`100%` on mandatory set

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. replay semantic assertions
2. browser/manual comparison against golden expectations

Alert threshold:

any confirmed miss on standing mandatory pack

Stop/escalate threshold:

any confirmed miss on mandatory gate set

### KPI-07 Unsupported / No-Data / Permission Envelope Correctness

Purpose:
measure whether safe terminal responses are explicit, correct, and policy-compliant.

Formula:

`envelope correctness = correct envelopes / validated envelope turns`

Operational target:

`>= 98%`

Promotion gate:

`>= 98%`

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. replay suites
2. browser/manual unsupported and clarification packs
3. incident review

Alert threshold:

`< 99%`

Stop/escalate threshold:

`< 98%`

### KPI-08 Write-Safety Violations

Purpose:
measure whether any write action bypasses required safety, permission, or confirmation controls.

Formula:

`write-safety violations = count of confirmed write safety breaches`

Operational target:

`0`

Promotion gate:

`0`

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. write safety replay packs
2. browser/manual write checks
3. incident register

Alert threshold:

any confirmed violation

Stop/escalate threshold:

any confirmed violation

### KPI-09 P95 Latency by Class

Purpose:
measure runtime responsiveness by behavior class.

Formula:

`P95 latency = 95th percentile end-to-end turn latency for the measured class`

Measured classes in first Phase 4 version:

1. ranking and KPI read flows
2. multiturn follow-up flows
3. unsupported or clarification flows

Operational target:

class-specific SLA to be finalized once runtime signal map confirms field availability

Interim rule:

track and trend now, do not use as release blocker until signal completeness is confirmed

Owner:
`AI Runtime Engineering` with platform support

Primary source of truth:

runtime audit and latency fields

Alert threshold:

P95 worsens by `> 20%` versus current baseline for two consecutive windows

Stop/escalate threshold:

breach of finalized class-specific SLA once approved

Threshold source:

`Contract-gated after SLA approval`

### KPI-10 Fallback Rate

Purpose:
measure how often the assistant depends on repair, planner clarify, or fallback envelopes instead of direct correct resolution.

Formula:

`fallback rate = fallback or repair turns / eligible turns`

Operational target:

trend downward and hold stable after each approved release

Initial working threshold:

`<= 10%` pending signal-map confirmation

Owner:
`AI Runtime Engineering`

Primary source of truth:

runtime audit outcomes and response envelope types

Alert threshold:

`> 10%` trailing 7 days

Stop/escalate threshold:

`> 12%` or sudden spike with confirmed user-visible regression

Threshold source:

`Phase 4 operational control KPI`

### KPI-11 Incident Reopen Rate

Purpose:
measure whether supposedly closed failures are returning.

Formula:

`incident reopen rate = reopened incidents / closed incidents`

Operational target:

`<= 5%`

Owner:
`AI Runtime Engineering`

Primary source of truth:

incident register

Alert threshold:

`> 5%`

Stop/escalate threshold:

two or more reopened Tier 1 or Tier 2 incidents in one review window

Threshold source:

`Phase 4 operational control KPI`

### KPI-12 Incident Closure Discipline

Purpose:
measure whether incidents are being closed with proper regression evidence instead of informal resolution.

Formula:

`closure discipline rate = incidents with full closure evidence / closed incidents`

Required closure evidence:

1. root cause recorded
2. fix record recorded
3. regression asset linked
4. reruns recorded
5. closure rationale recorded

Operational target:

`100%`

Owner:
`AI Runtime Engineering`

Primary source of truth:

incident register and review pack

Alert threshold:

any incident closed without full evidence

Stop/escalate threshold:

any Tier 1 or Tier 2 incident closed without full evidence

Threshold source:

`Phase 4 operational control KPI`

### KPI-13 Audit Envelope Completeness

Purpose:
measure whether every actionable turn carries the required audit evidence needed for control, review, and rollback decisions.

Formula:

`audit completeness = actionable turns with complete required audit fields / actionable turns`

Operational target:

`100%`

Promotion gate:

`100%` on actionable turns

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. runtime audit surfaces
2. replay debug traces
3. release-gate review packs

Alert threshold:

any missing required audit field on an actionable turn

Stop/escalate threshold:

any confirmed actionable-turn audit completeness miss in a gated review window

Threshold source:

`Contract-gated`

### KPI-14 Behavior-Class Mandatory Coverage

Purpose:
measure whether the replay manifest still covers the required mandatory class set.

Formula:

`mandatory coverage = covered mandatory classes / total mandatory classes`

Operational target:

`>= 95%`

Promotion gate:

`>= 95%`

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. replay manifest summaries
2. release-gate reports

Alert threshold:

`< 100%` in routine weekly review

Stop/escalate threshold:

`< 95%` in formal gate window

Threshold source:

`Contract-gated`

### KPI-15 Behavior-Class First-Run Pass Rate

Purpose:
measure first-run pass health for each mandatory behavior class.

Formula:

`class first-run pass rate = first-run passes for class / total first-run cases for class`

Operational target:

`>= 90%` for each mandatory class

Promotion gate:

`>= 90%` for each mandatory class

Owner:
`AI Runtime Engineering`

Primary source of truth:

1. replay class summaries
2. release-gate reports

Alert threshold:

`< 92%` for any mandatory class in routine review

Stop/escalate threshold:

`< 90%` for any mandatory class in formal gate window

Threshold source:

`Contract-gated`

## 5. KPI Use Rules

These rules apply to every KPI above:

1. first-run scoring only for formal gate use
2. replay and browser evidence must not contradict each other silently
3. any metric definition change requires versioned documentation update
4. any missing source-of-truth field must be declared, not guessed
5. manual evidence can confirm a problem even when replay is green

## 6. Metrics Review Outputs

Each weekly review should classify the system as one of:

1. `Stable`
2. `Watch`
3. `At Risk`

Suggested rule:

1. `Stable`
   all stop thresholds clear, no severe incident trend, no unresolved contradiction between replay and browser evidence
2. `Watch`
   one or more alert thresholds breached, but no stop threshold breached
3. `At Risk`
   any stop threshold breached, any write-safety violation, or repeated contradiction between browser and replay evidence

## 7. Known Gaps Before Full Operationalization

These gaps are expected and should be resolved in the next Phase 4 document:

1. exact runtime field source for latency and retry metrics
2. exact source field for fallback and planner-clarify counting
3. whether current audit envelope fully captures all required operational counts
4. whether browser/manual evidence should be summarized per class or per standing pack

These are not blockers for approving this KPI spec. They are inputs for the runtime signal map.

## 8. Immediate Next Step

After approving this document, the next practical step is:

create the runtime signal map and tie every KPI in this document to an actual field, log path, or manual evidence source.
