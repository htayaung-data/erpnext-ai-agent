# Enterprise Shared UI Component Implementation Contract v1

Date: 2026-04-28
Status: Mandatory implementation contract for future ERP workspace pages
Parent standard: `enterprise-shared-ui-component-standard-v1.md`
Reference implementation: Sales Console on `feature/erpnext-ui-design`

## 1. Purpose

This document turns the Enterprise Shared UI Component Standard into an execution contract.

The parent standard explains the philosophy.

This contract defines what future implementation agents must actually build, verify, and document before a workspace page is considered enterprise-grade.

Use this document when:

1. starting a new workspace
2. adding a new page to an existing workspace
3. changing shared components
4. reviewing whether a page is complete
5. preparing a prompt for another AI agent

Do not use this document as optional advice.

It is the practical gate that protects the project from page-by-page drift.

## 2. Operating Decision

Future ERP UI work must follow this order:

1. define the business role and job
2. choose the page archetype
3. choose the shared shell
4. define the backend payload contract
5. define route ownership
6. define permission and mutation boundaries
7. implement shared behavior first
8. implement page-specific business logic second
9. verify browser behavior
10. update docs before calling the page complete

If a proposed page cannot pass these steps, do not start coding it yet.

### 2.1 Decision Priority

When standards appear to conflict, use this priority order:

1. ERP truth and permissions
2. business role safety
3. route ownership
4. shared component consistency
5. visual clarity
6. implementation convenience

Implementation convenience never wins over ERP truth, permissions, route ownership, or user clarity.

### 2.2 Change Control

This contract may change, but not casually.

Any future change to this contract must record:

1. what changed
2. why the old rule was insufficient
3. which pages or workspaces are affected
4. whether existing pages must be updated
5. whether the parent standard also needs an update
6. whether SERA audit notes must be amended

Do not silently change the standard to justify one page.

If one page needs an exception, record it as a waiver instead of weakening the whole standard.

### 2.3 Waiver Rule

Waivers are allowed only when a rule cannot be followed safely or economically for a specific business reason.

Every waiver must include:

1. the exact rule being waived
2. the page or component affected
3. the business reason
4. the risk
5. the compensating control
6. the date or condition for revisiting it

Waivers must not be used for:

1. visual preference
2. speed alone
3. avoiding shared component work
4. opening raw ERP routes when productized routes already exist

## 3. Non-Negotiable Enterprise Gates

Every page must satisfy these gates.

### Gate 1: Business Purpose

The page must have a clear business job.

Required answer:

1. who uses the page
2. what decision or action the page supports
3. what the page intentionally does not support
4. what native ERP page remains the source of transaction truth

Fail examples:

1. adding a page because a doctype exists
2. adding a menu item because a native ERP report exists
3. adding a card because there is empty space

### Gate 2: Archetype Declaration

Every page must declare one primary archetype before implementation.

Allowed archetypes:

1. workspace home
2. directory
3. queue
4. report
5. managed document execution
6. draft create
7. create/edit profile
8. drill-down detail
9. guard/restricted/empty state

If a page appears to need multiple archetypes, split the page or define one primary archetype and secondary sections explicitly.

### Gate 3: Shared Shell First

Use an existing shared shell unless there is a documented reason not to.

Default shell choices:

1. workspace home: console runtime
2. directory and queue: list page shell
3. report: report page shell
4. saved document: child page shell on managed ERP form
5. draft create: child page draft readiness pattern on managed ERP form
6. create/edit profile: worklist form-panel pattern
7. drill-down detail: worklist detail pattern
8. guard state: worklist or report guarded state pattern

Do not create a one-off layout for a reusable problem.

### Gate 4: Backend Owns Business Truth

Frontend should render business decisions.

Backend should decide business truth.

Backend payload must define:

1. page identity
2. summary data
3. filter definitions
4. metrics
5. rows or sections
6. action targets
7. empty or restricted states
8. permission flags
9. route keys

Frontend must not infer permission, workflow, credit, stock, or accounting truth from raw DOM state.

### Gate 5: Productized Route First

If a productized route exists, every card, row, button, search result, and linked record must use it.

Allowed route classifications:

1. productized route
2. managed native form
3. governed native fallback
4. deferred route notice
5. blocked route

Raw native ERP navigation is not automatically acceptable.

### Gate 6: Refresh-Safe Deep Links

Any page that depends on a record, queue, report, or filter must survive browser refresh.

Required:

1. route key in URL
2. record key in URL when the page is record-specific
3. backend can reload state from URL or safe filters
4. missing context shows a guarded state
5. invalid context shows a safe unavailable state

Do not depend only on `frappe.route_options` or transient JavaScript state.

### Gate 7: One Active Navigation State

The sidebar must show one source of truth.

Required:

1. only one selected item
2. queue routes highlight their parent directory
3. detail/edit routes highlight their parent directory
4. managed document forms highlight their business family
5. report routes either have an approved Reports destination or no active item by design

Never show native ERP module menus mixed with productized workspace navigation for normal users.

### Gate 8: Permission-Safe Mutation

Any create, update, delete, submit, cancel, or workflow action must be server-checked.

Required:

1. role check
2. doctype permission check
3. record permission check where applicable
4. allowed-field check
5. document status and workflow check where applicable
6. saved truth returned to frontend
7. error message that does not lose user input

Delete is exceptional and must not appear by default.

### Gate 9: Calm Action Hierarchy

Each context should have one primary action.

Action order and emphasis must match the task:

1. commit actions: strongest
2. business next actions: visible only when valuable
3. navigation actions: low emphasis
4. communication actions: available where business needs them
5. utilities: quiet
6. destructive actions: hidden unless explicitly approved

Do not show a grid of equal action cards for low-value actions.

### Gate 10: Business Copy Earns Space

Helper text must have business value.

Allowed copy intents:

1. action
2. blocked
3. decision
4. empty
5. exception
6. missing
7. readonly
8. risk
9. warning

Remove copy that only explains the implementation.

User-facing copy must avoid implementation language unless the page is explicitly for administrators or implementers.

Avoid these terms in normal workspace UI:

1. native
2. productized
3. route
4. raw ERP
5. implementation
6. permission scope
7. console-owned

Prefer business-facing terms instead:

1. standard report
2. standard list
3. current access scope
4. current Sales Console scope
5. related records
6. document view
7. activity area

### Gate 11: Visual Stability

The page must not visibly fight itself.

Required:

1. no duplicate sidebars
2. no duplicate search boxes
3. no two selected menu items
4. no major first-load jump
5. no layout shake after data arrives
6. no unnecessary blank panels
7. collapsed sidebar remains aligned

If a page requires hard refresh to look correct, it is not complete.

### Gate 12: Verification Evidence

Every completed page must leave evidence.

Required:

1. syntax check for touched JavaScript
2. compile check for touched Python
3. manual browser script or smoke result
4. route ownership decision
5. permission/mutation decision if data changes
6. docs update or explicit no-docs-needed note

### Gate 13: Role Matrix Evidence

Every workspace must define the role assumptions it was built for.

At minimum, record:

1. normal operational user
2. manager or approver user
3. restricted or read-only user where the workflow has permission boundaries
4. admin or finance owner where fields or actions are intentionally excluded

For mutation pages, verify:

1. authorized role can complete the action
2. unauthorized role cannot see or cannot execute the action
3. backend rejects unauthorized mutation even if the button is manually invoked
4. restricted states do not leak hidden business data

No mutation page can receive `Final Grade` without role matrix evidence.

### Gate 14: Token And Business Data Formatting Discipline

Shared UI must stay visually and commercially consistent across workspaces.

Required:

1. colors, shadows, radii, spacing, and typography choices use shared tokens or shared component classes where available
2. new visual tokens are documented before they become reusable
3. page-specific hard-coded colors or dimensions are allowed only for documented one-off business reasons
4. currency, quantity, percentage, date, and datetime values use ERP-aware formatting helpers or backend-formatted values
5. dates must be unambiguous for the user's locale and business context
6. timezone-sensitive values must say what business date or operating window they represent

Do not let each page invent its own visual or data-formatting language.

## 4. Route Target Contract

Pages must emit abstract targets, not raw route decisions, wherever possible.

Allowed target shapes:

### 4.1 Productized Page Target

Use for stable workspace pages.

```json
{
  "kind": "page",
  "route": "sales-console"
}
```

### 4.2 Worklist Target

Use for directories, queues, detail pages, and editor pages owned by the workspace shell.

```json
{
  "kind": "worklist",
  "queue_key": "customer_detail",
  "filters": {
    "customer": "Customer Name"
  }
}
```

Rules:

1. queue keys use backend registry names
2. record-specific worklists must include the record key
3. frontend route owner must encode record keys into the URL where refresh safety requires it

### 4.3 Report Page Target

Use for productized report shell pages.

```json
{
  "kind": "report_page",
  "report_key": "sales_order_analysis"
}
```

Rules:

1. report key must exist in backend registry
2. route must survive refresh
3. row/cell links must still use route ownership rules

### 4.4 Managed Native Form Target

Use only for approved native forms enhanced by workspace runtime.

```json
{
  "kind": "form",
  "doctype": "Sales Order",
  "name": "SAL-ORD-2026-00001"
}
```

Rules:

1. target doctype must be approved as managed native form or mapped to productized route
2. sidebar must remain workspace-owned
3. scoped search must remain workspace-owned
4. document actions must use shared action policy

### 4.5 Native List Target

Use only as governed fallback.

```json
{
  "kind": "list",
  "doctype": "Sales Invoice",
  "filters": {
    "customer": "Customer Name"
  }
}
```

Rules:

1. productized directory must be preferred when it exists
2. fallback must be intentional
3. fallback should be low-emphasis or restricted-state recovery
4. fallback must not open incomplete native creation flows

### 4.6 New Document Target

Use only when native ERP creation remains the approved transaction owner.

```json
{
  "kind": "new_doc",
  "doctype": "Quotation"
}
```

Rules:

1. allowed only for approved create flows
2. page must be managed by workspace sidebar/runtime if opened inside workspace journey
3. print/email/downstream actions stay inactive until save where appropriate

### 4.7 API Method Target

Use for controlled create/edit profile operations.

```json
{
  "kind": "api_method",
  "method": "erp_workspace_ui.sales_console.worklist.save_sales_console_customer_profile",
  "collect_fields": true,
  "stay_on_success": true
}
```

Rules:

1. method must be whitelisted intentionally
2. method must perform server-side permission checks
3. method must validate allowed fields
4. method must return saved truth
5. success behavior must be explicit

## 5. Sidebar Contract

The sidebar is a stable destination map, not a list of every possible action.

Required definition per workspace:

1. workspace title or company name
2. utility actions
3. stable destination items
4. active-state map
5. collapsed-state behavior
6. route ownership helper

Stable destination examples:

1. Overview
2. Quotations
3. Sales Orders
4. Customers
5. Items

Rules:

1. do not add a sidebar item for every queue
2. do not add Reports until a real reports destination exists
3. do not show native module menu for normal workspace users
4. do not show duplicate workspace home items
5. utility actions must align visually with menu items
6. active state must be shared-route based, not page-specific CSS

Required active-state mapping template:

| Route family | Active item |
| --- | --- |
| workspace home | overview item |
| directory route | matching directory item |
| queue route | parent directory item |
| detail route | parent directory item |
| editor route | parent directory item |
| managed document form | business family item |
| report route | report item if approved, otherwise none by design |

## 6. Page Archetype Contracts

### 6.1 Workspace Home Contract

Purpose:

The operating entry point for the role.

Required content:

1. concise hero or title area
2. role-relevant priority metrics
3. limited quick actions
4. priority queues
5. report shortcuts only when business-useful
6. no raw report dump

Primary actions:

1. create approved transaction drafts
2. open productized directories
3. open productized queues
4. open productized reports

Verification:

1. quick actions route correctly
2. cards do not duplicate the sidebar without purpose
3. page reload keeps sidebar stable
4. empty data state remains meaningful

### 6.2 Directory Contract

Purpose:

Show all visible records in a business family.

Required payload:

1. `page.title`
2. `summary.title`
3. `controls.fields`
4. `controls.actions`
5. `metrics`
6. `results.columns`
7. `results.rows`
8. `action_targets`

Required filters:

1. business-family status where useful
2. date range where volume or timing matters
3. keyword search where identity lookup matters
4. role or territory scope only if it changes visible records

Rules:

1. default should not silently show only an operational slice
2. show latest 50 unless pagination or another limit is designed
3. row target must use productized route if available
4. filter actions stay close to filters
5. button order is Apply, Reset, Refresh

### 6.3 Queue Contract

Purpose:

Show a focused operational slice of a directory.

Required payload:

1. same base payload as directory
2. queue key in route
3. parent active sidebar mapping
4. empty-state explanation for the specific slice

Rules:

1. queue must not pretend to be all records
2. queue must not become a sidebar destination by default
3. queue rows use the same table component as directory where possible
4. queue title should name the business condition

### 6.4 Report Contract

Purpose:

Answer a business question over a selected window.

Required payload:

1. report key
2. title
3. filter definitions
4. metrics
5. rows or chart data
6. action targets for linked cells
7. empty state
8. route guard for unknown report key

Rules:

1. do not expose raw ERP reports without product purpose
2. row links must use route owner
3. chart is optional, not decorative
4. report route must survive refresh

### 6.5 Managed Document Execution Contract

Purpose:

Help users understand and act on a saved ERP document while ERPNext remains transaction truth.

Required elements:

1. compact document header
2. meaningful status chips
3. restrained action band
4. attention/guidance only when business-relevant
5. native document tabs where still needed
6. Connections section governed by route ownership

Rules:

1. do not build a wall of action cards
2. do not expose generic native create buttons from Connections
3. print/email may remain native
4. delete/duplicate must not be casually exposed
5. document tables must not hide key business names

### 6.6 Draft Create Contract

Purpose:

Help users complete and save a new ERP transaction.

Required elements:

1. readiness summary
2. required-field signals
3. save as primary commit action
4. disabled or hidden actions that require save
5. decision support only where it helps the user commit safely

Rules:

1. readiness must not duplicate every native field
2. stock support must be line-level and quiet
3. page must not flicker between native and custom layout
4. print/email are not active until save unless explicitly supported by ERP

### 6.7 Create/Edit Profile Contract

Purpose:

Allow controlled maintenance of a business entity.

Required payload:

1. mode: `new` or `edit`
2. title
3. allowed fields
4. select options
5. save action target
6. cancel/back target
7. optional business boundary note
8. permission state

Rules:

1. form must use approved safe fields only
2. save must persist to ERP truth
3. save should stay on page unless the user chooses navigation
4. edit route must include record key
5. create and edit copy must differ
6. do not show unrelated result/list panels

### 6.8 Drill-Down Detail Contract

Purpose:

Show one entity with current posture and recent activity.

Required payload:

1. record key in route
2. identity title
3. classification meta
4. posture metrics
5. focused activity filters
6. activity table
7. row action targets
8. edit action if role allows
9. back target

Rules:

1. refresh must reload the same record
2. table ordering should match primary business need
3. group-by is optional and should not replace useful recency
4. rows must route through route owner

### 6.9 Guard/Restricted/Empty Contract

Purpose:

Explain why normal content is unavailable.

Required payload:

1. condition title
2. short business explanation
3. one safe recovery action where useful
4. no technical stack details
5. no hidden data leakage

Rules:

1. missing route key is a guard state
2. no permission is a restricted state
3. no matching records is an empty state
4. backend failure is an error state

## 7. Component Contracts

### 7.1 Filter Command Strip

Required:

1. filters and actions in one visual group
2. Apply first
3. Reset second
4. Refresh third
5. date inputs use calendar affordance
6. labels match filter meaning

Label rules:

1. use `Activity Type` for mixed activity filtering
2. use `Document Type` for literal document categories
3. use `Status` for document status
4. use `Date Start` and `Date End` when filtering date windows
5. avoid vague `View` unless it truly switches business views

### 7.2 Action Band

Required action fields:

1. key
2. label
3. category
4. target or handler
5. disabled state where relevant
6. disabled reason where visible

Allowed categories:

1. `commit`
2. `primary_business_action`
3. `business_next_step`
4. `follow_up`
5. `linked_document`
6. `reference_document`
7. `supporting_navigation`
8. `navigation`
9. `communicate`
10. `utility`
11. `destructive`

Rules:

1. shared policy decides what appears in the top band
2. linked document noise should move to Connections or be hidden
3. follow-up appears only when active or valuable
4. destructive action requires explicit approval

### 7.3 Data Table

Required row shape:

1. row key
2. cells by column key
3. optional row actions
4. action target registered outside cell copy

Rules:

1. first column identifies the record
2. meta text must be useful
3. row state must use text labels, not color only
4. item/customer names must not disappear
5. row open target must be productized if available

### 7.4 KPI Cards

Required:

1. label
2. value
3. optional business meta
4. tone only when meaningful

Rules:

1. warning tone only for real attention
2. zero values remain honest
3. card counts must match table/filter scope or say otherwise
4. do not show metrics the role cannot act on or interpret

### 7.5 Connection Cards

Required:

1. group title distinct from child card title
2. linked count
3. view target
4. create target only when approved

Rules:

1. optional empty links are hidden unless absence matters
2. create buttons require role, route, and complete downstream form
3. linked documents route through route owner
4. child cards must not visually look identical to group headers

### 7.6 Business Notes

Required:

1. note text
2. note intent
3. business reason

Rules:

1. default neutral notes do not render
2. implementation-facing notes are removed
3. note must reduce confusion, risk, or next-action uncertainty
4. do not keep copy just to balance whitespace

### 7.7 Design Tokens

Required:

1. use shared component classes for repeated cards, buttons, filters, tables, and shells
2. use shared CSS variables or documented tokens for repeated colors, spacing, radius, shadows, and typography
3. document any new reusable token in the parent standard or shared runtime notes
4. keep token names semantic, not page-specific

Good token intent examples:

1. primary action
2. attention state
3. neutral border
4. card radius
5. page max width

Avoid:

1. one-off hex colors copied between pages
2. one-off pixel widths for common shells
3. visual changes that only work on one screen size
4. page-specific token names such as `sales-order-orange-line`

### 7.8 Business Data Formatting

Required:

1. money values include currency where business context needs it
2. percentages identify what they measure
3. quantities preserve useful precision without visual noise
4. dates use one consistent business format per workspace
5. date ranges identify start and end meaning
6. empty numeric values use a clear placeholder instead of misleading zero

Rules:

1. do not mix backend-formatted and frontend-formatted money on the same page without a reason
2. do not show ambiguous dates such as `01/02/2026` when the audience could misread them
3. do not round business-critical values in a way that changes the decision
4. use ERP/company currency and locale settings where available

## 8. Permission And Data Mutation Matrix Template

Every mutation page must document this matrix.

| Action | Role | Backend method | Doctype touched | Fields touched | Permission check | Save behavior | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Example save customer profile | Sales Manager | whitelisted method | Customer, Contact | name, group, territory, phone, email | role plus doctype permission | stay on page and return saved truth | medium |

Required decisions:

1. who can read
2. who can create
3. who can update
4. who can delete
5. which fields are allowed
6. which fields are controlled by Admin or Finance
7. which actions remain native ERP only

## 9. Route Ownership Matrix Template

Every workspace must maintain a route matrix.

| Source page | Element | Expected target | Actual target | Classification | Decision | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| Directory | Row open | Productized detail | worklist detail route | productized route | accept | none |

Required classifications:

1. productized route
2. managed native form
3. governed native fallback
4. deferred route
5. blocked route

## 10. Browser Verification Script Template

Run this for every new workspace or major page family.

Required checks:

1. open workspace home
2. open every sidebar destination
3. open one directory row
4. open one detail or editor route
5. hard refresh every major route
6. use browser Back and Forward
7. collapse and expand sidebar
8. use scoped search shortcut
9. apply and reset filters
10. test empty or restricted state if available
11. test save action if the page mutates data
12. verify no native ERP menu/search leaks into normal workspace journey

Record:

1. route tested
2. expected behavior
3. actual behavior
4. pass/fail
5. screenshot note if manual
6. fix or deferred decision

## 11. Definition Of Done

A page is done only when all are true:

1. business purpose is documented
2. archetype is declared
3. shared shell is used
4. backend payload contract is defined
5. route ownership is documented
6. permission boundaries are documented
7. visual stability is checked
8. accessibility basics are checked
9. browser verification is recorded
10. token and data-formatting discipline is checked
11. docs match code

A workspace is done only when:

1. every page passes page definition of done
2. no critical native route leakage remains
3. no unsafe mutation remains
4. role matrix assumptions are documented
5. shared component changes are documented
6. deferred items are listed
7. the branch is committed

### 11.1 Final Grade Labels

Use these labels when reviewing a page, workspace, or shared component.

`Final Grade`

The work is ready to become a reference pattern.

Required:

1. all non-negotiable gates pass
2. no known high or medium risk remains unresolved
3. browser verification is recorded
4. docs match code
5. role matrix evidence exists where permissions matter
6. token and business-data formatting discipline is checked
7. any waivers are documented and low risk

`Conditional Pass`

The work may continue, but it must not become a reusable reference yet.

Allowed only when:

1. remaining issues are low risk
2. the issue is documented
3. a fix or revisit point is defined
4. the issue does not affect route ownership, permissions, or data truth

`Not Ready`

The work must not be copied to another workspace.

Use this label when:

1. route ownership is unclear
2. permissions are not proven
3. save or mutation behavior is unreliable
4. browser refresh or back navigation breaks the page
5. UI requires hard refresh to appear correct
6. helper text, actions, or routes would confuse normal business users

### 11.2 Promotion Rule

A page may become a golden reference only after:

1. it receives `Final Grade`
2. its reusable pattern is documented in this contract or the parent standard
3. at least one browser verification pass confirms normal and refresh behavior
4. there is no open SERA blocker for that page family

Do not promote a page to reference status because it merely looks good in one screenshot.

## 12. AI Feature Deferral Rule

AI features are intentionally deferred until the workflow is stable.

Allowed now:

1. record possible AI opportunities
2. identify pages where AI may provide real decision value
3. note data and permission dependencies
4. avoid duplicate AI design between workspace UI and AI Assistant branch

Not allowed now:

1. adding AI widgets just because space exists
2. using AI to replace core ERP validation
3. letting AI create, submit, cancel, or delete records without explicit governed workflow
4. adding AI prompts before route, permission, and page stability are complete

Future AI notes should answer:

1. what user pain AI solves
2. what data AI needs
3. what role may use it
4. what action AI may suggest
5. what action AI may not take
6. where human confirmation is required

## 13. Next Workspace Prompt Requirements

Any prompt given to a future AI agent must include:

1. workspace business scope
2. target roles
3. page list with archetypes
4. shared shells to reuse
5. route ownership rules
6. permission and mutation boundaries
7. forbidden patterns
8. acceptance checklist
9. browser verification script
10. instruction to update docs to match code

The prompt must explicitly say:

1. do not create page-specific hacks for shared problems
2. do not expose native ERP pages when productized routes exist
3. do not add create/update/delete actions without server-side permission checks
4. do not add helper text unless it has business intent
5. do not start AI features until core workflow is stable

## 14. Relationship To Sales Console

Sales Console is the current reference implementation, but this contract is cross-workspace.

Copy from Sales Console:

1. shared route ownership discipline
2. sidebar stability
3. scoped search posture
4. directory versus queue split
5. guarded deep-link behavior
6. restrained action-band policy
7. business-copy reduction
8. permission-safe customer profile pattern

Do not blindly copy:

1. sales-only labels
2. sales-only document relationships
3. sales-only metrics
4. Sales Console page order
5. unfinished deferred behavior

The future standard is the combination of:

1. this implementation contract
2. the parent shared UI standard
3. SERA audit findings
4. current code truth
