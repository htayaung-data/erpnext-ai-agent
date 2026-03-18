# Phase 4 Incident Operations Contract

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: live operational incident handling model for Phase 4  
Status: first operational incident contract after Phase 3 closure

## 1. Purpose

This document turns the Phase 3 incident template into a real operating process.

The purpose is simple:

1. when something goes wrong, we know who owns it
2. we know how fast it must be triaged
3. we know what evidence is required
4. we know when it is safe to close

This is an operations contract, not a runtime artifact.

## 2. Incident Types Covered

This contract applies to:

1. replay-detected gate failures
2. browser/manual failures on standing packs
3. live user-visible defects
4. safety or permission failures
5. phase-contract breaches
6. reopened previously closed failures

It does not apply to:

1. planned future enhancements
2. already-approved deferred Tier-3 hardening items unless they regress or widen
3. feature requests that are not current defects

## 3. Severity Model

### P1

Definition:

critical incident with business, safety, or governance impact.

Examples:

1. write-safety violation
2. permission or tenant boundary breach
3. wrong-report escape on Tier 1 flow with business impact
4. repeated production failure with no safe fallback
5. contract breach in runtime core modules

### P2

Definition:

high-severity incident with user-visible quality impact, but not a critical safety/compliance breach.

Examples:

1. wrong report on supported read flow
2. broken follow-up context on approved class
3. output-shape failure on mandatory browser pack
4. unsupported or clarification behavior incorrect on approved class

### P3

Definition:

low-severity issue or deferred hardening item that does not block current controlled use.

Examples:

1. repeated transform edge-case drift
2. cosmetic or presentation inconsistency outside critical flows
3. known deferred hardening item with current mitigation

## 4. Risk Tier Mapping

Severity and risk tier are related but not identical.

Use this rule:

1. severity describes business impact now
2. risk tier describes how much regression rigor is required

Default mapping:

1. P1 -> usually `Tier 1`
2. P2 -> usually `Tier 1` or `Tier 2`
3. P3 -> usually `Tier 3`

If severity and tier differ, record the reason explicitly.

## 5. Incident States

Each incident must use one of these states:

1. `Open`
2. `In Progress`
3. `Blocked`
4. `Awaiting Validation`
5. `Closed`

State rules:

1. `Open`
   defect confirmed but not yet assigned for active fix
2. `In Progress`
   owner is actively investigating or fixing
3. `Blocked`
   waiting on dependency, environment, or decision
4. `Awaiting Validation`
   fix is present, waiting for replay/manual confirmation
5. `Closed`
   required evidence completed and reviewed

## 6. Ownership Rules

### Primary Owner

Initial default owner:

`AI Runtime Engineering`

### Secondary Participants

1. browser/manual validation owner
2. product/business reviewer
3. platform/deployment owner

### Assignment Rule

Assign primary owner based on dominant root-cause surface:

1. resolver/spec/ontology/capability issue -> AI Runtime Engineering
2. browser/manual parity issue -> browser/manual validation owner plus AI Runtime Engineering
3. latency or deployment issue -> platform/deployment owner plus AI Runtime Engineering
4. permission/security issue -> AI Runtime Engineering with governance escalation

## 7. Triage SLA

### P1

1. acknowledge within `4 hours`
2. triage within `1 business day`
3. containment or rollback decision within `1 business day`

### P2

1. acknowledge within `1 business day`
2. triage within `2 business days`
3. remediation plan within `3 business days`

### P3

1. acknowledge within `2 business days`
2. triage within `5 business days`
3. may be deferred if mitigation is documented

## 8. Required Incident Record

Every incident record must include:

1. incident ID
2. severity
3. risk tier
4. owner
5. user-visible symptom
6. expected behavior
7. behavioral class
8. primary incident family
9. root-cause summary
10. impacted shared surfaces
11. fix summary
12. files changed, if any
13. regression assets linked
14. reruns performed
15. closure rationale
16. residual risk, if any

Base template:

[step14_incident_register_template.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step14_incident_register_template.md)

## 9. Closure Rules

An incident may be closed only when all applicable items below are complete.

### For P1 and P2

1. root cause is written clearly
2. fix stays inside contract boundary
3. targeted regression asset exists
4. required shared-surface reruns are recorded
5. browser/manual validation is recorded when user-visible behavior changed
6. residual risk is either zero or explicitly accepted

### For P3

One of the following must be true:

1. issue is fully fixed and validated
2. issue is intentionally deferred with mitigation and revisit trigger

### Closure Prohibition

Do not close an incident when:

1. replay is green but browser evidence still shows failure
2. fix is based on unapproved runtime hardcoding
3. root cause is unknown
4. required reruns were skipped without written justification

## 10. Regression-Link Requirement

Every P1 and P2 incident must leave behind permanent regression protection.

Required minimum:

1. unit or module test when the failure is code-local
2. replay asset or replay assertion when the failure is behavior-visible
3. browser/manual evidence when the failure is user-visible

Rule:

no important incident closes without linked regression evidence.

## 11. Escalation Rules

Escalate immediately when any of the following occurs:

1. any write-safety violation
2. any permission or tenant boundary breach
3. repeated wrong-report incident on Tier 1 flow
4. browser/manual contradiction against green replay on a critical flow
5. runtime contract breach in protected core modules
6. unresolved P1 after `5 working days`

Escalation target in this first version:

1. AI Runtime Engineering lead
2. product/business reviewer
3. platform or governance owner if needed

## 12. Reopen Rules

An incident must be reopened when:

1. the same user-visible failure returns
2. the same regression pack fails again
3. browser evidence disproves the previous closure decision
4. a deferred risk becomes a live defect

When reopened:

1. keep the same incident ID if it is the same defect family
2. record reopen reason
3. update regression-link evidence
4. review whether prior closure was too weak

## 13. Weekly Review Integration

Every weekly operational review must summarize:

1. new incidents
2. reopened incidents
3. closed incidents
4. open P1 and P2 incidents
5. incidents without linked regression assets

Weekly review template:

[step14_phase3_weekly_quality_review_template.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step14_phase3_weekly_quality_review_template.md)

## 14. Stop and Rollback Alignment

This incident contract must stay aligned with enterprise stop/rollback rules.

Operational meaning:

1. incident handling must support rollback decisions
2. metric breach plus incident evidence can block promotion
3. serious incidents override convenience or schedule pressure

## 15. Deferred Hardening Rule

A deferred hardening item is acceptable only when all are true:

1. it is not a current release blocker
2. mitigation exists
3. revisit trigger is written
4. it is clearly documented in closure or review notes

If any deferred item becomes a live user-visible defect, convert it into an incident immediately.

## 16. Immediate Operating Recommendation

For the first Phase 4 version:

1. use this contract with the existing incident template
2. require incident records for all new P1 and P2 issues
3. include incident summary in every weekly review
4. do not automate incident dashboards until the process is being followed consistently
