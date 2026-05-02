# Sales Console Enterprise Readiness Audit Mini-Phase Plan

Date: 2026-04-28
Status: Active plan before next workspace implementation
Depends on: `enterprise-shared-ui-component-standard-v1.md`
Reference implementation: Sales Console on `feature/erpnext-ui-design`

## 1. Purpose

This plan defines how to audit Sales Console for enterprise readiness without trying to fix everything in one pass.

The goal is quality first.

The audit should prove that Sales Console is a reliable golden reference before another workspace copies its patterns.

This plan intentionally separates:

1. product judgment
2. route ownership
3. security and permissions
4. visual stability
5. shared component health
6. page-specific polish
7. documentation freeze

## 2. Operating Rule

Do not audit and refactor everything at once.

Use mini-phases.

Each mini-phase must produce one of these outcomes:

1. pass
2. pass with deferred notes
3. blocked by shared-platform issue
4. blocked by business decision

Only shared-platform blockers should be fixed immediately.

Page-specific cosmetic improvements should be recorded unless they damage enterprise quality or will be copied into the next workspace.

## 3. Mini-Phase Overview

Recommended order:

1. `SERA-0` Audit Setup And Baseline
2. `SERA-1` Route Ownership And Navigation Safety
3. `SERA-2` Security, Permission, And Data Mutation Safety
4. `SERA-3` Visual Stability And Shared Component Quality
5. `SERA-4` Page Archetype Audit By Family
6. `SERA-5` Cross-Page Fix Pass
7. `SERA-6` Freeze, Golden SOP Promotion, And Next Workspace Gate

SERA means Sales Console Enterprise Readiness Audit.

## 4. SERA-0 Audit Setup And Baseline

### Goal

Confirm what is being audited and prevent branch or environment confusion.

### Scope

1. branch and worktree
2. latest commit
3. live server sync status
4. docs index
5. current untracked files
6. page inventory
7. shared runtime inventory

### Required Evidence

Record:

1. branch name
2. latest commit hash
3. audited worktree path
4. whether live site is synced
5. list of Sales Console managed routes
6. list of shared runtime files used by Sales Console

### Exit Criteria

This phase passes only when:

1. audit is confirmed on `feature/erpnext-ui-design`
2. code and docs being audited are from the same commit or consciously noted as different
3. page inventory is complete enough to avoid missing major surfaces

### Fix Policy

No product fixes in this phase.

Only correct branch or environment mistakes.

## 5. SERA-1 Route Ownership And Navigation Safety

### Goal

Prove that Sales Console owns its user journey and does not accidentally leak users into confusing raw ERP routes.

### Scope

Audit:

1. left sidebar
2. scoped search
3. home cards
4. directory row links
5. queue row links
6. report row links
7. saved document actions
8. Connections tab links
9. Customer Detail activity links
10. Customer Create/Edit back links
11. browser back and forward
12. hard refresh on deep links

### Questions

For every navigation element:

1. Does a productized route exist?
2. If yes, does the action use it?
3. If no, is native fallback intentional and safe?
4. Is active sidebar state correct?
5. Does the route survive refresh?
6. Does browser back return to a stable page?
7. Does the user see one source of truth?

### Required Evidence

Create a route matrix with:

1. source page
2. element label
3. expected target
4. actual target
5. route type: productized, native fallback, blocked, deferred
6. decision
7. fix required or not

### Exit Criteria

This phase passes only when:

1. no high-value action accidentally opens raw ERP when productized route exists
2. native fallback routes are documented
3. sidebar active state is correct across managed routes
4. direct refresh works for detail/edit/report/queue routes

### Fix Policy

Fix immediately if:

1. a common action goes to wrong page
2. a route loses context on refresh
3. sidebar shows duplicate or wrong active state
4. native menu leaks into workspace routes

Defer if:

1. target page is not productized yet and native fallback is acceptable
2. the issue is low-frequency and documented

## 6. SERA-2 Security, Permission, And Data Mutation Safety

### Goal

Prove the workspace does not bypass ERPNext authority, role permissions, workflow, accounting, or stock truth.

### Scope

Audit:

1. Customer Create
2. Customer Edit
3. Customer Detail
4. draft quotation actions
5. draft sales order actions
6. saved document actions
7. print and email entry points
8. follow-up actions
9. report/worklist backend methods
10. smoke-test files

### Questions

For every mutation:

1. Is permission checked server-side?
2. Is the field allowed for the role?
3. Does the save persist to ERP truth?
4. Are linked records updated intentionally?
5. Does the UI return saved truth?
6. Are errors handled without losing data?
7. Is delete hidden unless explicitly approved?
8. Are workflow and submit rules native-owned?

For every display:

1. Is business data escaped?
2. Are restricted records hidden safely?
3. Are restricted states explained safely?
4. Are secrets absent from committed files?

### Required Evidence

Create a permission and mutation matrix with:

1. action
2. role assumption
3. backend method
4. doctypes touched
5. fields touched
6. permission check
7. save result
8. risk level
9. decision

### Exit Criteria

This phase passes only when:

1. no custom mutation bypasses native ERP truth
2. Customer Create/Edit save correctly
3. Sales User versus Sales Manager boundaries are documented
4. no session token or secret is staged
5. print/email limitations are documented as configuration-dependent, not code failure

### Fix Policy

Fix immediately if:

1. a custom save does not persist
2. a user can mutate disallowed fields
3. a secret is present
4. a button exposes unsafe delete/duplicate/create behavior

Defer if:

1. a feature depends on future email account setup
2. a role-policy decision is needed from business leadership

## 7. SERA-3 Visual Stability And Shared Component Quality

### Goal

Prove Sales Console feels premium, stable, and reusable at the shared-component level.

### Scope

Audit shared components:

1. sidebar
2. workspace home cards
3. list shell
4. report shell
5. child page shell
6. action band
7. filter command strip
8. form panel
9. detail page header
10. connection cards
11. search dialog
12. empty and restricted states

### Questions

For every shared component:

1. Does it align consistently?
2. Does it avoid unnecessary text?
3. Does it avoid first-load jumping?
4. Does it work collapsed and expanded?
5. Does it behave on narrow width?
6. Does it use premium but restrained visual hierarchy?
7. Would we confidently copy this component to another workspace?

### Required Evidence

Create a component audit table with:

1. component
2. current quality level
3. shared or page-specific issue
4. screenshot needed or not
5. fix now or defer
6. standard rule affected

### Exit Criteria

This phase passes only when:

1. no shared component has an obvious premium-quality blocker
2. sidebar collapsed and expanded states are stable
3. filter/action alignment is acceptable
4. form panel alignment is acceptable
5. first-load movement is documented and fixed if severe

### Fix Policy

Fix immediately if:

1. component instability appears across multiple pages
2. visual defect would be copied into next workspace
3. native and custom UI both appear at the same time
4. search opens duplicate dialogs

Defer if:

1. the issue is page-local and low impact
2. the improvement is taste-level polish without operational risk

## 8. SERA-4 Page Archetype Audit By Family

### Goal

Audit each Sales Console page as a business surface, grouped by archetype.

### Page Families

#### Family A: Workspace Entry

Pages:

1. Sales Console home
2. sidebar
3. scoped search

Audit focus:

1. role clarity
2. quick actions
3. priorities
4. search behavior
5. left navigation

#### Family B: Directories And Queues

Pages:

1. Quotations directory
2. Sales Orders directory
3. Customers directory
4. Items directory
5. approval queues
6. blocker queues
7. follow-up queues

Audit focus:

1. filter quality
2. all-record versus operational-slice clarity
3. row navigation
4. table readability
5. empty states

#### Family C: Customer Profile Surfaces

Pages:

1. Customer Detail
2. Customer Create
3. Customer Edit

Audit focus:

1. direct route reload
2. safe-field boundary
3. create versus edit copy
4. save behavior
5. detail activity navigation
6. Sales User versus Sales Manager authority

#### Family D: Draft Documents

Pages:

1. New Quotation
2. New Sales Order

Audit focus:

1. draft readiness
2. save action
3. print/email disabled posture
4. form stability
5. stock availability readiness for future phase
6. avoiding busy UI

#### Family E: Saved Execution Documents

Pages:

1. saved Quotation
2. saved Sales Order
3. Delivery Note where managed
4. Sales Invoice where managed

Audit focus:

1. summary header
2. action band
3. attention cards
4. details tab
5. connections tab
6. native fallback boundaries
7. print/email entry points

#### Family F: Reports

Pages:

1. Sales Order Analysis
2. Sales Person Target Variance
3. Quotation Trends
4. Lost Quotations
5. Collections Status
6. Item Sales History

Audit focus:

1. report purpose
2. filter compactness
3. metric clarity
4. table value
5. safe row navigation

### Required Evidence

For each page family, record:

1. pass/fail summary
2. top business risk
3. top UI risk
4. top route risk
5. fix now list
6. defer list

### Exit Criteria

This phase passes only when every family has:

1. known quality status
2. no unknown route risks
3. no unknown mutation risks
4. no obvious shared-component blocker

## 9. SERA-5 Cross-Page Fix Pass

### Goal

Fix only the issues that should be corrected before the next workspace copies the pattern.

### Fix Priority

Fix in this order:

1. security and permission defects
2. route ownership defects
3. data persistence defects
4. shared component instability
5. major visual alignment defects
6. confusing business copy
7. page-local polish

### Rules

Do:

1. fix shared runtimes first
2. apply to all affected pages
3. keep changes small and testable
4. update docs immediately

Do not:

1. start stock availability in this phase
2. start another workspace in this phase
3. redesign every page by taste
4. mix unrelated fixes in one commit if they can be separated

### Exit Criteria

This phase passes when:

1. high and medium blockers from SERA-1 to SERA-4 are resolved or consciously deferred
2. validation checks pass
3. browser smoke confirms the fix
4. docs reflect final behavior

## 10. SERA-6 Freeze, Golden SOP Promotion, And Next Workspace Gate

### Goal

Declare whether Sales Console is ready to be used as the golden reference.

### Outputs

Create or update:

1. Sales Console enterprise readiness audit report
2. page freeze notes
3. deferred improvements
4. next workspace implementation prompt
5. shared component standard if new rules were discovered

### Gate Decision

Use one of these decisions:

1. `Ready for next workspace`
2. `Ready with deferred low-risk improvements`
3. `Not ready: shared blockers remain`
4. `Not ready: business decision required`

### Exit Criteria

Next workspace can begin only when:

1. Sales Console has no unresolved high-risk route issue
2. Sales Console has no unresolved high-risk permission issue
3. shared component standard is current
4. known deferred work is documented
5. next workspace prompt references the standard and audit results

## 11. Suggested Execution Order

Recommended practical workflow:

1. First session: complete `SERA-0` and `SERA-1`
2. Second session: complete `SERA-2`
3. Third session: complete `SERA-3`
4. Fourth session: complete `SERA-4` Family A to C
5. Fifth session: complete `SERA-4` Family D to F
6. Sixth session: complete `SERA-5` fix pass
7. Seventh session: complete `SERA-6` freeze and next workspace prompt

This can be compressed if a phase is clean.

It should not be compressed if route ownership, permissions, or shared components show risk.

## 12. Immediate Next Step

Start with `SERA-0`.

Produce a baseline note with:

1. current branch and commit
2. current live deployment assumption
3. managed route inventory
4. shared runtime inventory
5. page family inventory
6. known untracked files that should stay out of commits

Then move to `SERA-1` only after baseline is clear.
