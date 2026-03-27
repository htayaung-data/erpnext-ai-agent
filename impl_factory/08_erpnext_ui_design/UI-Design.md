# UI Design

Status: active single source of truth for ERPNext UI design in the UI workstream  
Scope: enterprise-grade overview for the full workspace and console portfolio  
Phase: overview architecture only; detailed console design will be handled one workspace at a time later

## 1. Purpose

This document defines the top-level UI design direction for the ERPNext user experience.

It is not an MVP note.
It is not a prototype brief.
It is the design authority for building a serious enterprise-grade ERPNext operating experience for this business.

This document should answer:

1. what the UI is trying to achieve
2. how the workspace and console portfolio should be structured
3. how AI should assist users without overwhelming them
4. what enterprise-grade experience standards must be preserved
5. what the prioritized rollout should look like

Detailed design for each console should be created later under this document, not in place of it.

## 2. Source Hierarchy

This document is the UI design source of truth for this branch.

It is grounded in these reference sources:

1. [reference_pack_reading_notes_2026-03-27.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/reference_pack_reading_notes_2026-03-27.md)
2. [ERP Governance and Operating Architecture.pdf](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/ERP%20Governance%20and%20Operating%20Architecture.pdf)
3. [Mingalar_ERP_Implementation_Matrix.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_Implementation_Matrix.xlsx)
4. [Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx)
5. [Mingalar_ERP_Workspace_Configuration_Matrix.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_Workspace_Configuration_Matrix.xlsx)

If future design notes disagree with this document, this document wins until it is explicitly revised.

## 3. Design Mission

The UI mission is not to redesign ERPNext for style.
The UI mission is to transform ERPNext into a role-based operating environment that is:

1. simpler for daily work
2. more controlled for approvals and exceptions
3. more focused for each role family
4. more auditable and governable
5. more efficient through carefully placed AI assistance

The target experience should feel:

1. enterprise-safe
2. task-first
3. role-aware
4. branch-aware
5. warehouse-aware
6. fast to act in
7. difficult to misuse casually

## 4. Core Design Position

The UI should be built on these non-negotiable positions:

1. ERPNext remains the operating system
2. role-based workspaces become the primary daily entry points
3. standard ERPNext modules remain available in the background during early rollout
4. actions come first, approvals and controls come second, reports come third
5. visibility should follow permission, branch, warehouse, territory, and approval scope
6. the system should reduce clutter rather than increase novelty
7. AI should assist with judgment, preparation, prioritization, and efficiency
8. AI should not dominate the workspace or replace the primary operating UI

## 5. Enterprise-Grade Experience Principles

### 5.1 Usability Principles

1. one workspace should represent one real job family, not one ERP module
2. the first screen should immediately expose the role’s most common next actions
3. the second layer should expose approvals, queues, exceptions, and operational blockers
4. the third layer should expose reports and insight views
5. users should not need to browse generic module menus to perform routine work

### 5.2 Control Principles

1. the UI must reinforce segregation of duties
2. creators and approvers should not have the same visual affordances by default
3. restricted warehouses and sensitive finance actions must remain visually and behaviorally constrained
4. management workspaces should emphasize review and approval rather than direct transaction handling
5. approval state must be visible where it matters, not buried inside document history

### 5.3 Information Architecture Principles

1. branch context must be obvious
2. warehouse context must be obvious where stock is involved
3. queue and workload visibility must be native to the workspace
4. important alerts should be structured and actionable, not just decorative badges
5. dashboards should be operational first and analytical second

### 5.4 Performance Principles

1. first-load experience should prioritize summary cards and essential actions
2. high-volume users should be able to reach their primary task within one click from the workspace
3. search and quick actions should reduce navigation depth
4. the interface should support dense operational use without feeling cramped

### 5.5 Accessibility And Reliability Principles

1. strong contrast and legible hierarchy are required
2. keyboard-friendly operation should be preserved for power users
3. state, status, and approval meaning should never depend only on color
4. branch, warehouse, and approval context should be explicit text, not implied
5. the UI should fail safely if AI assist or non-critical enhancements are unavailable

## 6. Target Workspace Portfolio

The normalized workspace portfolio should consist of nine primary consoles.

This portfolio is intentionally revised beyond the raw reference wording where needed to better fit a serious trading and distribution operating model.

The key consultant adjustment is:

1. add a dedicated cross-functional operations layer
2. tighten workspace names so they describe real operating responsibility
3. avoid vague or overly generic workspace labels

### 6.1 First-Wave Workspaces

These should be designed and implemented first because they support the highest daily operational volume and cross-functional control needs.

1. `Sales Console`
2. `Procurement & Replenishment Console`
3. `Warehouse & Logistics Console`
4. `Finance Control Console`
5. `Operations Control Console`

### 6.2 Second-Wave Workspaces

These should be designed at overview level now, but implemented after first-wave validation.

1. `Executive Oversight Console`
2. `Returns & Service Console`
3. `ERP Governance Console`
4. `HR & Admin Console`

### 6.3 Rationalization Of The Reference Model

The raw references also mention `Commercial and Operations Workspace` and `Showroom Workspace`.

For the enterprise overview, these are normalized as follows:

1. `Commercial and Operations Workspace`
   - redefined as `Operations Control Console`
   - separated from executive oversight because daily cross-functional control is not the same job as executive review
2. `Showroom Workspace`
   - handled as a focused sales execution mode or view inside `Sales Console`

This preserves the operational intent while avoiding workspace sprawl and management/operations role confusion.

### 6.4 Final Workspace Portfolio

The final enterprise workspace portfolio is:

1. `Executive Oversight Console`
2. `Operations Control Console`
3. `Sales Console`
4. `Procurement & Replenishment Console`
5. `Warehouse & Logistics Console`
6. `Finance Control Console`
7. `Returns & Service Console`
8. `ERP Governance Console`
9. `HR & Admin Console`

## 7. Common Workspace Anatomy

Every primary console should follow a consistent architecture so users learn one pattern and then apply it everywhere.

### 7.1 Workspace Layout Zones

Each console should be structured in this order:

1. context header
   - workspace name
   - role identity
   - branch context
   - warehouse or approval scope where relevant
2. primary actions row
   - most common transactions
   - quick-create actions
   - role-safe shortcuts
3. work queue zone
   - pending tasks
   - approvals
   - exceptions
   - overdue items
4. operational insight zone
   - KPI cards
   - status cards
   - branch or warehouse summaries
5. report and review zone
   - role-relevant reports
   - deeper analysis entry points
6. AI assist zone
   - compact
   - contextual
   - collapsible
   - never the dominant panel

### 7.2 Cross-Workspace Shell Elements

All consoles should share these shell elements:

1. global search
2. quick action launcher
3. branch indicator
4. approval inbox indicator
5. notification center
6. recent work / continue work area
7. optional AI assist entry point

## 8. AI Design Position

AI should be integrated where it improves efficiency, prioritization, and decision quality.

AI should not:

1. interrupt primary workflows constantly
2. force users into chat for routine actions
3. hide the underlying ERP state
4. produce vague advisory text with no operational value
5. become a decorative novelty layer

AI should:

1. reduce reading time
2. reduce navigation effort
3. reduce missed exceptions
4. reduce repetitive analysis
5. help users decide faster with controlled context

## 9. Global AI Assist Principles

### 9.1 Interaction Principles

1. AI must be contextual, not universal by default
2. AI must be compact by default and expandable on demand
3. AI outputs must reference real ERP context
4. AI suggestions must respect the user’s permission scope
5. AI should recommend, summarize, compare, or prioritize before it tries to explain broadly

### 9.2 Placement Principles

AI can appear in these patterns:

1. workspace insight card
2. queue summary panel
3. inline recommendation section
4. side assistant drawer
5. approval or exception briefing panel

AI should generally not appear as:

1. a full-screen assistant replacing the workspace
2. a mandatory chat composer on every page
3. an always-open floating overlay

### 9.3 Governance Principles

1. AI must never bypass workflow or approval rules
2. AI must not create false urgency or hidden automation
3. AI suggestions must be reversible and reviewable
4. AI-generated summaries must not overwrite source data
5. AI should be auditable where it affects decisions or approvals

## 10. Enterprise AI Assist Layer

The recommended enterprise AI layer should provide these capabilities across the UI:

1. daily work summary
   - what needs attention first
2. exception briefing
   - why this item is risky, delayed, blocked, or unusual
3. approval briefing
   - what the approver needs to know before acting
4. comparative summarization
   - supplier comparison, customer context, overdue grouping, stock anomaly grouping
5. next-best-action suggestion
   - practical operational guidance, not general motivational text
6. context carry-forward
   - user should not need to re-explain the same operational situation repeatedly

## 11. Workspace Overview And AI Strategy

### 11.1 Executive Oversight Console

Purpose:

1. management dashboard for approvals, exceptions, branch comparison, stock exposure, and receivable exposure

Primary experience:

1. report-first
2. approval-first
3. exception-first
4. minimal routine transaction clutter

Primary content:

1. branch sales comparison
2. receivable exposure
3. stock value and stock-risk summary
4. major pending approvals
5. cross-functional exception queue

AI assist:

1. daily executive briefing:
   - top risks
   - delayed approvals
   - branch anomalies
2. approval impact summary:
   - what decision is needed
   - what financial or stock impact is visible
3. exception narrative:
   - concise explanation of unusual patterns without forcing report drilling first

### 11.2 Sales Console

Purpose:

1. daily selling, quotation, sales order follow-up, customer follow-up, and pipeline execution

Primary experience:

1. customer-first
2. quotation-first
3. low-friction transaction entry
4. visible approval status

Primary content:

1. create opportunity
2. create quotation
3. create sales order
4. customer follow-up queue
5. open quotations and open orders
6. customer history and balance warnings

AI assist:

1. pre-meeting or pre-call customer brief
2. quote-follow-up priority suggestions
3. risk nudge:
   - overdue balance
   - credit-risk signal
   - unusual discount context
4. suggested next action after opening a customer or quotation context

### 11.3 Procurement & Replenishment Console

Purpose:

1. replenishment, supplier comparison, RFQ flow, supplier quotation handling, and purchase order preparation

Primary experience:

1. supplier-first
2. reorder-need visibility
3. approval-aware purchasing workflow

Primary content:

1. create RFQ
2. create supplier quotation
3. create purchase order
4. review reorder triggers
5. review expected arrivals and delayed supply

AI assist:

1. supplier comparison summary
2. reorder urgency summary
3. delayed-arrival risk explanation
4. approval briefing for unusual or higher-value purchasing

### 11.4 Warehouse & Logistics Console

Purpose:

1. receiving, transfer execution, dispatch, movement monitoring, stock control, and queue-based warehouse work

Primary experience:

1. queue-first
2. movement-first
3. warehouse-scope-specific
4. low clutter

Primary content:

1. stock entry and movement actions
2. pending receipts
3. transfer queue
4. warehouse stock views
5. transit and returns visibility for authorized users

AI assist:

1. queue prioritization:
   - what should move first
2. transfer anomaly summary
3. stock exception brief:
   - damaged
   - delayed
   - mismatch-prone
4. receiving or dispatch prep summary for active work batches

### 11.5 Finance Control Console

Purpose:

1. receivables, payables, payment preparation, invoice handling, journal review, and financial control execution

Primary experience:

1. party-balance-first
2. approval-aware
3. finance-focused
4. separated from warehouse and CRM clutter

Primary content:

1. payment entry
2. sales and purchase invoice access
3. journal review
4. receivable aging
5. payable aging
6. payment approval queue

AI assist:

1. receivable priority summary
2. payment risk review summary
3. cash-control brief
4. unusual journal or exception explanation
5. branch exposure snapshot for finance reviewers

### 11.6 Operations Control Console

Purpose:

1. cross-functional daily control of blockers, escalations, delayed fulfillment, transfer friction, approval bottlenecks, and branch operating issues

Primary experience:

1. blocker-first
2. queue-and-exception-first
3. cross-functional
4. operational, not executive

Primary content:

1. orders blocked by stock or approval
2. delayed transfers and in-transit exceptions
3. purchase arrival risk affecting sales commitments
4. branch bottlenecks and escalations
5. cross-functional queue health

AI assist:

1. daily operations control briefing
2. blocker clustering and root-cause summary
3. next-best-resolution suggestion
4. branch exception comparison
5. risk of delay or service failure across linked workflows

### 11.7 Returns & Service Console

Purpose:

1. issue handling, complaint management, returns follow-up, warranty follow-up, and service case coordination

Primary experience:

1. issue-first
2. customer-context-first
3. minimal unrelated navigation

Primary content:

1. open complaints
2. return and service records
3. customer history
4. follow-up queue

AI assist:

1. issue triage summary
2. case history summary
3. recommended next follow-up
4. exception alert when a case is aging or blocked unusually

### 11.8 ERP Governance Console

Purpose:

1. controlled configuration, user management, role assignment, permission management, workflow review, workspace governance, and setup integrity

Primary experience:

1. governance-and-control-first
2. not for routine business use

Primary content:

1. users
2. roles
3. user permissions
4. workflows
5. workspaces
6. department and designation governance
7. access review and configuration review

AI assist:

1. permission impact summary
2. workflow change briefing
3. access-review anomaly detection
4. workspace configuration completeness checklist
5. governance drift warning

### 11.9 HR & Admin Console

Purpose:

1. employee, leave, attendance, department, designation, and administrative support tasks

Primary experience:

1. people-and-admin-only
2. isolated from commercial and stock-heavy flows

Primary content:

1. employee maintenance
2. leave and attendance handling
3. designation and department review
4. HR operational reports

AI assist:

1. attendance anomaly summary
2. leave backlog summary
3. onboarding or setup checklist guidance
4. department or designation cleanup suggestions where structure is inconsistent

## 12. Cross-Cutting Visibility Model

Visibility must not be purely cosmetic.
The UI should reflect real operating scope.

### 12.1 Scope Indicators

Relevant workspaces should visibly show:

1. current branch scope
2. warehouse scope where applicable
3. approval authority level
4. restricted vs review-only mode where relevant

### 12.2 Workspace Restriction Model

1. sales users should not live in finance or stock-heavy navigation
2. warehouse and logistics users should not live in CRM or finance-heavy navigation
3. finance users should not live in operational stock movement navigation
4. executive users should not be forced through transaction-heavy module workspaces
5. operations control users should see cross-functional exceptions without being turned into technical administrators
6. ERP governance tools should be isolated from normal business navigation

## 13. Form Design Position

The form strategy should follow the workspace strategy.

### 13.1 Principle

1. workspaces reduce navigation burden
2. forms reduce cognitive burden

### 13.2 Priority Order

The form simplification sequence should follow this order:

1. Quotation
2. Sales Order
3. Purchase Order
4. Stock Entry
5. Payment Entry

### 13.3 Form Rules

1. show role-relevant fields first
2. collapse technical or infrequent sections
3. surface workflow and approval status clearly
4. preserve full ERP detail when needed, but not as the default visual burden

## 14. Enterprise Visual Direction

The visual direction should feel calm, serious, operational, and modern without becoming decorative.

### 14.1 Visual Tone

1. clean enterprise density
2. strong hierarchy
3. restrained color
4. role-oriented emphasis
5. operational clarity over visual novelty

### 14.2 What To Avoid

1. dashboard clutter
2. excessive card noise
3. oversized metrics with weak actionability
4. AI panel dominance
5. consumer-style gimmicks

## 15. Rollout Strategy

This UI should be rolled out in controlled stages, not a single large visual rewrite.

### 15.1 Stage 1

1. design and build first-wave workspaces:
   - Sales
   - Procurement & Replenishment
   - Warehouse & Logistics
   - Finance Control
   - Operations Control
2. assign them to role-slot users
3. validate daily use patterns

### 15.2 Stage 2

1. refine first-wave workspaces
2. reduce dependency on generic standard workspaces
3. introduce targeted form simplification

### 15.3 Stage 3

1. build second-wave workspaces:
   - Executive Oversight
   - Returns & Service
   - ERP Governance
   - HR & Admin
2. expand AI assist where it has proven value

## 16. What This Overview Intentionally Does Not Do Yet

This overview does not yet define:

1. pixel-level layout
2. field-by-field form redesign
3. ERPNext workspace JSON structures
4. final implementation code
5. detailed AI interaction flows per document screen

Those should be designed next, one console at a time, under this architecture.

## 17. Immediate Next Design Step

The next UI design document should be the first detailed console specification.

Recommended order:

1. `Sales Console`
2. `Procurement & Replenishment Console`
3. `Warehouse & Logistics Console`
4. `Finance Control Console`
5. `Operations Control Console`
6. `Executive Oversight Console`
7. `Returns & Service Console`
8. `ERP Governance Console`
9. `HR & Admin Console`

## 18. Final Design Judgment

The correct enterprise UI direction is:

1. preserve ERPNext as the system foundation
2. introduce role-based workspaces as the operating layer
3. simplify navigation before over-customizing forms
4. keep approvals, exceptions, and reports visible by role
5. integrate AI as a compact decision-support and efficiency layer
6. design for controlled rollout, auditability, and long-term maintainability

This is the overview architecture that should guide all later console-level design work.
