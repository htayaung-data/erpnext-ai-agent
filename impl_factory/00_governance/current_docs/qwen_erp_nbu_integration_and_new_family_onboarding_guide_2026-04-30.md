# Qwen ERP NBU Integration And New Family Onboarding Guide

Status: design lock for future-family integration
Date: 2026-04-30
Scope: how existing and future business families integrate with the Natural Business Understanding control layer

## 1. Purpose

This guide defines how a business family must integrate with NBU.

NBU must be a project-wide semantic control layer, not a finance-only, customer-risk-only, or current-problem-only feature.

When future families such as HR, CRM, procurement analytics, service operations, or manufacturing are added, they should not require rewriting NBU.

They should plug into NBU through governed metadata, evidence contracts, authority policies, and tests.

## 2. Core Rule

NBU understands natural language through the lightweight model.

Registries validate and govern that understanding.

A new family must therefore provide enough metadata and evidence shape for NBU to answer these questions:

1. what business domain does this family belong to
2. what user actions are supported
3. what capabilities/reports/composites can execute it
4. what fields, metrics, dimensions, rows, and entities are exposed
5. what follow-up references are safe
6. what requests require clarification
7. what requests are unsupported or authority-blocked
8. what test coverage proves the integration

## 3. Required Integration Layers

Every new family should integrate through these layers.

### 3.1 Business Domain And Ontology

Required metadata:

1. business concept ids
2. common natural-language aliases
3. extended aliases where useful
4. related domains
5. self-contained query hints if applicable

Examples:

1. HR: employee, payroll, attendance, leave, headcount
2. CRM: lead, opportunity, pipeline, conversion, campaign
3. Service: ticket, SLA, resolution time, complaint, escalation

Important rule:

Aliases help the model and validators, but they must not become the primary routing brain.

### 3.2 Capability Registration

Required metadata:

1. capability id
2. supported intent classes
3. supported report names or runtime source
4. supported metrics
5. supported dimensions
6. ontology concepts
7. default time scope behavior
8. activation state

NBU uses this to validate whether a model-proposed route is governed.

### 3.3 Report Or Runtime Source Registration

Required metadata:

1. report/source name
2. family id
3. supported metrics and dimensions
4. supported filters
5. required filters
6. period/as-of behavior
7. row identity fields
8. known display fields

NBU uses this to decide whether a current artifact can answer a follow-up or whether a requery is needed.

### 3.4 Family Or Composite Registration

Required when a family is not just one report.

Required metadata:

1. family id
2. family label
3. entity grain
4. primary metric policy
5. secondary/supporting metric policy
6. default variation policy
7. supported variation axes
8. blocked variations
9. follow-up affordances
10. activation state

Examples:

1. customer risk as-of composite
2. product commercial ranking
3. AR/AP working-capital health
4. future CRM pipeline health
5. future HR attendance risk snapshot

### 3.5 Evidence Contract

Every family must expose a normalized evidence artifact.

Required artifact fields:

1. `family_id`
2. `source_name`
3. `source_reports`
4. `period`
5. `filters`
6. `dimensions`
7. `metrics`
8. `sections`
9. `warnings`
10. row count
11. row identity strategy

Recommended section shapes:

1. `summary`
2. `ranked_rows`
3. `detail_rows`
4. `document_rows`
5. `bucket_rows`
6. `warehouse_rows`
7. `candidate_rows`

NBU cannot safely answer natural follow-ups unless the artifact exposes row identity and requested evidence clearly.

### 3.6 Follow-Up Affordances

A family must declare what follow-ups are safe.

Examples:

1. explain selected row
2. show aging breakdown
3. show stock by warehouse
4. open customer detail
5. open supplier detail
6. open item detail
7. switch sibling view
8. refine time scope
9. project columns
10. sort or limit rows

If a follow-up is not declared, NBU should clarify, requery through an approved source, or boundary.

### 3.7 Authority Boundary

Every family must classify authority-sensitive requests.

Common authority classes:

1. safe read
2. safe explanation
3. governed requery
4. recommendation
5. prediction
6. approval/action
7. policy decision
8. causal/driver analysis
9. hidden score/classification

For each non-safe authority class, the family must define:

1. allowed or blocked
2. required policy artifact
3. required evidence artifacts
4. approval state
5. safe user-facing boundary wording

This prevents a new family from accidentally answering unsupported questions such as:

1. who should we hire
2. will this customer default
3. approve credit
4. predict employee resignation
5. give a hidden risk score

### 3.8 Requery Plan

A family must document how NBU can recover when the current artifact lacks requested evidence.

Required fields:

1. source family
2. missing metric/dimension
3. compatible target family or report
4. required entity reference
5. required time scope
6. safe fallback if no compatible requery exists

Example:

1. current customer-risk table lacks credit limit
2. selected customer is known
3. customer detail or credit status source supports credit limit
4. NBU can execute governed requery

Counterexample:

1. current sales trend lacks causal evidence
2. no approved driver analysis artifact exists
3. NBU must boundary or ask for a supported trend/comparison view

### 3.9 Clarification Policy

A family must specify when to ask the user.

Clarify when:

1. target entity is unclear
2. row reference is ambiguous
3. requested metric has multiple governed meanings
4. requested period is required but missing
5. multiple candidate routes are close
6. user asks for a policy-sensitive action without enough detail

Clarification must be business-natural and should not expose internal contract names.

### 3.10 Test And UAT Registration

Every family must add coverage in three layers:

1. contract/unit tests
2. automated smoke or replay tests
3. manual browser UAT rows

Minimum test themes:

1. direct governed query
2. natural wording variant
3. noisy or typo variant
4. row/entity follow-up
5. missing evidence requery
6. unsupported authority boundary
7. context switch away from this family
8. stale-context guard
9. readable output formatting

## 4. NBU Family Onboarding Checklist

Before enabling a new family in production, complete this checklist.

### Metadata

1. business ontology concepts added
2. capability registry entry active
3. report/source registry entry active
4. family/composite registry entry active if needed
5. semantic aliases added only as validation/support metadata
6. supported metrics and dimensions declared
7. supported follow-up modes declared
8. authority boundaries declared

### Evidence

1. normalized artifact shape available
2. row identity available for ranked/list artifacts
3. selected-row evidence available when row explanations are supported
4. missing-field policy declared
5. provenance/source basis available where relevant

### NBU

1. family appears in NBU context summary
2. lightweight model can propose the family as a candidate interpretation
3. validator can accept/reject family candidate
4. action decision can route to the family
5. fallback renderer has family-safe wording
6. decision trace records the family decision

### Quality

1. unit tests added
2. smoke/replay tests added
3. manual UAT prompts added
4. shadow-mode comparison passes
5. controlled activation approved

## 5. Shadow-Mode Requirement

No new family should immediately control routing through NBU.

Activation sequence:

1. metadata registered
2. NBU sees the family in candidate context
3. shadow-mode interpretation logs candidates
4. validation confirms safe routes
5. automated tests pass
6. manual browser UAT passes
7. controlled activation enabled

This avoids breaking existing working behavior.

## 6. Unknown Request Handling

When users ask natural questions that are not yet supported, NBU should not fail with internal-looking text.

Allowed outcomes:

1. ask clarification
2. show supported alternatives
3. explain governed boundary
4. suggest a supported requery
5. mark as out of scope
6. log the unknown request for evaluation

Unknown requests should be logged with:

1. raw message
2. model candidate interpretations
3. selected action decision
4. validation failures
5. missing registry/evidence/policy reason
6. suggested backlog category

This is the enterprise feedback loop. It prevents endless ad hoc mapping.

## 7. New Family Example: HR

If HR is added later, it should not require NBU code rewrites.

Required additions:

1. ontology concepts: employee, attendance, leave, payroll, headcount
2. capabilities: employee_master_read, attendance_read, leave_read, payroll_read
3. reports or sources: Employee Master List, Attendance Summary, Leave Balance, Payroll Summary
4. evidence contracts: employee rows, attendance rows, leave balance rows
5. follow-up affordances: employee detail, leave breakdown, attendance trend
6. authority boundaries: hiring recommendation, termination prediction, salary approval
7. tests and UAT rows

After that, NBU should be able to interpret:

1. show employee attendance this month
2. tell me more about that employee
3. who has high leave balance
4. can we terminate this employee

The first three may be governed reads if supported.

The fourth must be authority-blocked unless an approved policy/action workflow exists.

## 8. New Family Example: CRM

If CRM is added later, required additions include:

1. ontology concepts: lead, opportunity, pipeline, conversion, campaign
2. capabilities: lead_read, opportunity_read, pipeline_read
3. reports or sources: Lead List, Opportunity Pipeline, Campaign Performance
4. evidence contracts: opportunity rows, stage breakdowns, conversion metrics
5. follow-up affordances: opportunity detail, stage breakdown, owner breakdown
6. authority boundaries: forecast guarantee, sales commitment, automatic discount approval
7. tests and UAT rows

NBU should then handle:

1. show open opportunities
2. which opportunities are stuck
3. why is this deal risky
4. will this deal close next month

The last request must be prediction-boundary unless an approved forecasting model exists.

## 9. Anti-Patterns

Do not onboard a family by:

1. adding a phrase-specific branch in `service.py`
2. creating one-off routing before metadata exists
3. relying on model output without validation
4. adding a report without evidence shape
5. allowing recommendations without authority policy
6. exposing internal contract language to users
7. skipping shadow mode
8. skipping manual browser UAT

## 10. Definition Of Done For Family Integration

A family is NBU-ready only when:

1. natural-language interpretation works in shadow mode
2. metadata validation accepts correct candidates
3. unsupported candidates are rejected safely
4. row/entity follow-ups work where declared
5. missing-evidence requery works where supported
6. authority boundaries are enforced
7. user-facing fallback is professional
8. tests and manual UAT cover the integration

## 11. Relationship To Current NBU Mini-Phase

This guide constrains the NBU implementation plan.

NBU-1 contract design must support future family onboarding.

NBU-2 runtime interpretation must receive family metadata in a compact, extensible format.

NBU-3 validation must work against registries rather than hardcoded families.

NBU-8 activation must support incremental family rollout.

Therefore, the first implementation slices should not be coded only around finance, customer risk, or current manual browser failures.

Those failures are the proof cases, not the architecture boundary.
