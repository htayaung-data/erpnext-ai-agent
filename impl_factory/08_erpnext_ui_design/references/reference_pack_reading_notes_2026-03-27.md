# ERPNext UI Reference Pack Reading Notes (2026-03-27)

## Purpose

This note records the first careful reading of the imported UI reference pack.

Raw files preserved here:

1. [ERP Governance and Operating Architecture.pdf](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/ERP%20Governance%20and%20Operating%20Architecture.pdf)
2. [Mingalar_ERP_Implementation_Matrix.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_Implementation_Matrix.xlsx)
3. [Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx)
4. [Mingalar_ERP_Workspace_Configuration_Matrix.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_Workspace_Configuration_Matrix.xlsx)

## Import Decision

The original source files existed in the AI worktree under the old `08_custom workspaces` folder.

To avoid cross-workstream interference, the raw pack was copied into the UI-owned references area instead of being renamed in the AI worktree.

## What Was Read Directly

The three Excel workbooks were read directly through workbook parsing.

The PDF was also read directly after local document-reading tools were installed in the user environment.

That means this note now reflects:

1. workbook structure and row-level content
2. PDF section structure
3. PDF guidance on governance, roles, permissions, workspace design, form behavior, reporting, and rollout

## PDF: Governance And Operating Architecture

Source:

1. [ERP Governance and Operating Architecture.pdf](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/ERP%20Governance%20and%20Operating%20Architecture.pdf)

Observed document structure:

1. company and operating footprint
2. organization, department, branch, warehouse, customer, product, and supplier governance
3. role and responsibility framework
4. permission and control architecture
5. approval hierarchy
6. role-based UI and workspace design
7. form simplification strategy
8. reporting architecture
9. implementation roadmap
10. ERP operational blueprint
11. workspace structure blueprint

Important business and operating conclusions:

1. the current ERP should be treated as a valid operating foundation, not as a demo system
2. the company is explicitly modeled as:
   - one legal entity
   - two principal branches
   - ten warehouses
   - multi-territory customer coverage
   - real retail and wholesale activity
3. the target operating model is matrix-style:
   - functional governance
   - branch execution
   - centralized control for pricing, approvals, and financial discipline

Important UI implications from the PDF:

1. UI should reflect branch execution with centralized oversight
2. UI must respect warehouse classification and access boundaries
3. UI design is explicitly defined as role-based simplification, not full visual redesign
4. workspaces should become the daily entry points while standard ERPNext modules remain in the background initially
5. one workspace should serve one role family or operating job, not one ERP module

Named workspace direction from the PDF:

1. `Executive Console`
2. `Sales Console`
3. `Procurement Console`
4. `Warehouse Console`
5. `Finance Console`
6. `Customer Service Console`
7. `HR and Admin Console`
8. `ERP Admin Console`

The PDF reinforces the same first-wave vs second-wave rollout pattern found in the workbook:

1. first wave:
   - Sales Console
   - Procurement Console
   - Warehouse Console
   - Finance Console
2. second wave:
   - Executive Console
   - Customer Service Console
   - HR and Admin Console
   - ERP Admin Console

Critical architectural design rules from the PDF:

1. action-first layout:
   - most common transactions first
2. control and review second:
   - approvals, exceptions, queue visibility
3. reporting third:
   - performance and analytical reports after actions and controls
4. limited visible options:
   - users should not land in cluttered module-wide navigation
5. standard modules should remain available, but not be the preferred daily starting point at first

Form simplification rules reinforced by the PDF:

1. sales forms should prioritize customer, items, quantity, rate, warehouse, delivery date, and approval/workflow status
2. warehouse forms should prioritize source warehouse, target warehouse, items, movement type, and workflow state
3. finance forms should prioritize party, account/payment type, amount, reference documents, and posting/workflow state
4. technical or low-frequency sections should be collapsed for routine users

Permission and approval implications from the PDF:

1. permissions must be designed by:
   - function
   - branch
   - warehouse
   - customer or territory scope
   - approval level
2. UI visibility should follow the same boundaries
3. approval routing is not optional decoration:
   - it is part of the operating model and should be visible in the workspace experience
4. segregation of duties matters:
   - creator and approver roles should not be blurred in the UI

Implementation pattern explicitly recommended by the PDF:

1. create first-wave workspaces only
2. assign them to the relevant role-slot users
3. populate them with top actions, top reports, and approval links
4. test actual user behavior
5. only then reduce standard-workspace visibility

This is a very strong signal that the UI workstream should begin with workspace architecture and controlled rollout, not with theme-first redesign.

## Workbook 1: Implementation Matrix

Source:

1. [Mingalar_ERP_Implementation_Matrix.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_Implementation_Matrix.xlsx)

Observed sheets:

1. `Implementation Matrix`
2. `Summary`
3. `Legend`

What it contains:

1. employee-to-role mapping for the real operating team
2. department normalization targets
3. branch scope and warehouse scope by user
4. ERP seat requirement and rollout phase hints

Important signals for UI design:

1. the system is branch-aware and warehouse-aware, not a flat single-office UI
2. user experience must respect operational scope:
   - all-branch management users
   - branch-limited operational users
   - warehouse-limited stock visibility users
3. the user base is not homogeneous:
   - managers need review visibility
   - transaction users need highly simplified operational entry points
4. the summary suggests a bounded rollout sequence, so UI rollout should also be staged

Important numbers seen in the workbook:

1. total employees: `22`
2. ERP users required: `18`
3. no ERP user initially: `4`

## Workbook 2: Role-Slot Permission Workflow Pack

Source:

1. [Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx)

Observed sheets:

1. `Overview`
2. `Role-Slot Plan`
3. `DocType Permissions`
4. `Workflow Spec`

What it contains:

1. development-stage placeholder role-slot accounts
2. seat ownership and go-live replacement guidance
3. DocType permission matrix by role profile
4. workflow routing rules by role and document type

Important UI implications:

1. the UI should be role-family-first, not person-first
2. the development environment should support role-slot testing before final named-user rollout
3. navigation should expose approvals and review queues only where the role actually owns them
4. the same document can mean very different UI needs for different roles:
   - executives mostly review
   - supervisors approve or escalate
   - transaction users create and update

Enterprise-grade takeaway:

1. workspace design cannot be separated from permission design
2. shortcut visibility, report visibility, and approval queue visibility should follow the role-slot and workflow model directly

## Workbook 3: Workspace Configuration Matrix

Source:

1. [Mingalar_ERP_Workspace_Configuration_Matrix.xlsx](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_Workspace_Configuration_Matrix.xlsx)

Observed sheets:

1. `Overview`
2. `Workspace Matrix`
3. `Navigation Rules`
4. `Form Priorities`
5. `Implementation Sequence`

This remains one of the most directly actionable UI references in the pack, but it is now clearly supported by the PDF rather than standing alone.

First-wave workspaces named in the workbook:

1. `Sales Console`
2. `Procurement Console`
3. `Warehouse Console`
4. `Finance Console`

Second-wave workspaces named in the workbook:

1. `Executive Console`
2. `Customer Service Console`
3. `HR and Admin Console`
4. `ERP Admin Console`

Strong design signals from this workbook:

1. replace generic ERPNext module entry points with role-based consoles
2. keep users inside their role family’s primary workspace for daily work
3. make approvals, reports, and exceptions visible from the workspace itself
4. reduce cross-module clutter, especially for warehouse and finance users
5. treat executives as report-first and exception-first users, not transaction-first users

Navigation rules that matter architecturally:

1. sales should avoid buying, stock, HR, and ERP settings as daily entry points
2. procurement should stay supplier- and purchasing-focused
3. warehouse should stay movement- and stock-focused
4. finance should stay party-balance- and payment-focused
5. management should see approvals, exceptions, and reports before routine transaction links

Form-priority implications:

1. quotation and sales order screens should surface customer, items, quantity, rate, warehouse, delivery date, and workflow state first
2. purchase order screens should prioritize supplier, items, rates, delivery date, and workflow state
3. stock entry screens should prioritize movement fields and operational context
4. payment entry screens should prioritize party, amount, references, and workflow state
5. advanced or technical sections should be collapsed or de-emphasized for routine users

Implementation-sequence implication:

1. workspace creation should happen before deeper form simplification
2. first-wave workspaces should be validated with role-slot users before second-wave expansion

## Consolidated UI Design Conclusions

Based on the imported references, the UI workstream should start from these assumptions:

1. the design target is role-based ERP navigation, not cosmetic theming
2. workspace architecture is the primary UI lever
3. first-wave operational consoles should be the first implementation target
4. role-slot permissions and approval paths must shape the UI structure from the start
5. form simplification should follow workspace rollout, not precede it
6. branch scope and warehouse scope are first-class UX boundaries
7. management UI should be exception-first and report-first, not transaction-first
8. standard ERPNext workspaces should remain initially, but move into the background as role-based consoles become the daily entry points
9. the right first implementation is navigation and workspace simplification, not broad custom page creation everywhere
10. the design should preserve ERPNext as the operating system while reshaping entry points, visibility, and prioritization for each role family

## Next Reading Priorities

The next UI documents should convert these references into implementation-ready notes for:

1. workspace architecture
2. navigation model
3. role-family entry points
4. first-wave rollout order
5. form simplification priorities
6. approval visibility model inside each workspace
7. branch-aware and warehouse-aware UI restrictions

## Current Judgment

The imported reference pack is coherent.

The PDF, the role-slot pack, the implementation matrix, and the workspace configuration matrix all point in the same direction:

1. preserve the existing ERP business footprint
2. formalize governance and permissions
3. simplify user experience through role-based workspaces
4. stage rollout in controlled waves
5. refine forms only after workspace entry points are working
