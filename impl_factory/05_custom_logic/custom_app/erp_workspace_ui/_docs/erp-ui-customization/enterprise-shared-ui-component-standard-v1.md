# Enterprise Shared UI Component Standard v1

Date: 2026-04-28
Status: Active standard for future ERP workspace implementation
Primary reference implementation: Sales Console
Source of truth: current code in `feature/erpnext-ui-design`
Mandatory companion: `enterprise-shared-ui-component-implementation-contract-v1.md`

## 1. Purpose

This standard converts the Sales Console implementation into a reusable enterprise UI contract for the next ERP workspaces.

The goal is not to copy the Sales Console page by page.

The goal is to copy the operating system underneath it:

1. stable workspace navigation
2. route ownership
3. shared page shells
4. shared action grammar
5. restrained premium visual language
6. permission-safe operations
7. business-first copy
8. consistent filters, tables, forms, and detail pages
9. reliable deep-link and refresh behavior
10. clear validation gates before a page is considered enterprise-grade

This document should be read before any new workspace implementation begins.

The companion implementation contract is mandatory for execution.

Use this document to decide what the product should feel like.

Use `enterprise-shared-ui-component-implementation-contract-v1.md` to decide whether a page is allowed to be called complete.

## 2. Mini-Phase Plan For This Standard

The standard itself should be implemented in controlled mini-phases.

### ESS-1 Current Truth Extraction

Goal:

Extract reusable patterns from the actual Sales Console code and docs.

Current completed inputs:

1. `sales-console-navigation-contract-v1.md`
2. `sales-console-business-copy-contract-v1.md`
3. `sales-console-mini-phase-6-operating-foundation.md`
4. shared runtime files under `public/js/runtime`
5. Sales Console worklist, report, child-page, and sidebar behavior

Output:

This standard becomes the cross-workspace contract.

### ESS-2 Component Taxonomy

Goal:

Define every shared component family by purpose, not by one page's appearance.

Required component families:

1. workspace sidebar
2. workspace home shell
3. directory and queue shell
4. report shell
5. child document shell
6. create and edit form shell
7. drill-down detail shell
8. action band
9. filter command strip
10. data table
11. KPI and summary cards
12. connection cards
13. readiness checklist
14. search
15. empty, blocked, loading, restricted, and unavailable states

### ESS-3 Visual And Interaction Contract

Goal:

Define what makes the interface premium and stable.

Required outputs:

1. spacing rules
2. card rules
3. button hierarchy
4. typography posture
5. color usage
6. hover/focus behavior
7. alignment rules
8. responsive behavior
9. motion limits
10. copy density limits

### ESS-4 Security And Permission Contract

Goal:

Protect ERP truth and user permissions.

Required outputs:

1. native ERP transaction boundary
2. create, read, update, delete rules by role
3. backend permission checks
4. route guard rules
5. safe native fallback rules
6. no hardcoded credentials or session tokens
7. no custom bypass of workflow, audit, or document status

### ESS-5 Page Acceptance Checklist

Goal:

Create a repeatable quality gate before a page is called complete.

Required outputs:

1. page-by-page UI checklist
2. route ownership checklist
3. permission checklist
4. refresh and browser navigation checklist
5. smoke-test checklist
6. docs update checklist

### ESS-6 Next Workspace Prompt Package

Goal:

Prepare the next implementation conversation or agent.

Required outputs:

1. workspace scope
2. page list
3. page archetype mapping
4. forbidden patterns
5. shared component references
6. acceptance checklist
7. manual browser test script

### ESS-7 Implementation Contract Hardening

Goal:

Make the standard enforceable enough for future agents and teams.

Current output:

`enterprise-shared-ui-component-implementation-contract-v1.md`

Purpose:

1. define non-negotiable enterprise gates
2. define route target contracts
3. define page archetype payload contracts
4. define component-level implementation rules
5. define permission and route matrix templates
6. define browser verification requirements
7. define the page and workspace definition of done

Decision:

Future workspace work must use the parent standard and the implementation contract together.

The parent standard alone is not sufficient for execution.

## 3. Enterprise Product Principles

These principles override page-local preferences.

### 3.1 Code Truth First

The implementation is the source of truth.

Docs must reflect code, not wishful design.

When code and docs disagree:

1. inspect the code
2. update the docs
3. only then decide whether code should change

### 3.1.1 Standard Governance

This standard is project infrastructure.

It should not be changed casually to justify one page.

Any change to this standard or its implementation contract must record:

1. the reason for the change
2. the affected page archetypes
3. whether existing Sales Console pages must be revisited
4. whether future workspace prompts must change
5. whether any SERA audit note must be amended

If one page needs a justified exception, record a waiver in the implementation contract instead of weakening the standard.

### 3.2 Shared First, Page Second

If two pages need the same behavior, implement it through a shared shell, helper, payload contract, or runtime.

Avoid page-specific fixes unless the business process is truly unique.

Page-specific CSS or JavaScript is allowed only when:

1. the behavior cannot be generalized safely
2. the exception is documented
3. it does not weaken the shared component contract

### 3.3 ERP Truth Is Not Replaced

The custom UI is an operating layer.

It must not replace ERPNext as the source of transaction truth.

Native ERP remains authoritative for:

1. save
2. submit
3. cancel
4. workflow transition
5. audit trail
6. document status
7. print generation
8. email sending
9. permissions
10. financial and stock calculations

The workspace UI owns:

1. discoverability
2. layout
3. route ownership
4. user guidance
5. filter posture
6. safe shortcuts
7. decision support

### 3.4 Premium Means Calm, Useful, And Predictable

Premium UI is not more decoration.

Premium UI means:

1. the next action is obvious
2. the page does not shake, flicker, or jump
3. business meaning is visible without reading long paragraphs
4. spacing is intentional
5. components align consistently
6. visual hierarchy is quiet but clear
7. dangerous or unavailable actions are not casually exposed
8. native ERP leakage is controlled

### 3.5 Business Copy Must Earn Its Space

Helper text is allowed only when it changes a business decision or reduces operational risk.

Do not write implementation-facing text for business users.

Avoid language such as:

1. native ERP
2. renderer
3. authoritative totals
4. route payload
5. workspace shell

Business users should see business language.

## 4. Page Archetypes

Every future workspace page must declare its archetype before implementation.

### 4.1 Workspace Home

Purpose:

Give the user a focused operating entry point.

Use for:

1. priorities
2. quick create
3. key queues
4. critical summaries
5. management-level shortcuts

Do:

1. show the most important work first
2. keep quick actions limited
3. route cards to productized pages where available
4. use role-aware ordering
5. keep the left sidebar stable

Do not:

1. repeat every page in both home and sidebar
2. use the home page as a raw report dump
3. add report links without a clear business purpose
4. show implementation notes

### 4.2 Directory Page

Purpose:

Show all visible records in a business family.

Examples from Sales Console:

1. Quotations
2. Sales Orders
3. Customers
4. Items

Do:

1. show all records the user can reasonably act on or review
2. provide stable filters
3. keep filter actions near filter controls
4. include status and keyword search where useful
5. support deep-link and refresh
6. open rows into productized routes where available

Do not:

1. silently limit records to a narrow operational slice
2. hide the reason records are missing
3. send users to generic ERP pages when a productized page exists
4. overload the sidebar with every filter variant

### 4.3 Queue Page

Purpose:

Show a focused operational slice of a directory.

Examples:

1. approvals waiting
2. orders due soon
3. quotations expiring
4. blocked records

Do:

1. highlight the parent directory in the sidebar
2. explain empty states only when useful
3. keep row actions minimal
4. preserve route key in the URL

Do not:

1. replace the directory page
2. pretend the queue is all records
3. add a sidebar item for every queue

### 4.4 Report Page

Purpose:

Answer a business question over a selected operating window.

Do:

1. name the report after the business question
2. keep filters compact
3. show summary metrics before table detail
4. use charts only if they improve the decision
5. allow row navigation only when it is business-safe

Do not:

1. expose raw ERP reports without product purpose
2. make every report look like a directory page
3. add chart complexity for visual decoration

### 4.5 Document Execution Page

Purpose:

Help users understand and act on a saved ERP document.

Examples:

1. saved Quotation
2. saved Sales Order
3. Delivery Note
4. Sales Invoice

Do:

1. keep the document header strong and compact
2. show only meaningful status chips
3. surface linked-record actions through a shared action model
4. preserve native document tabs where needed
5. own route navigation for linked records where productized pages exist

Do not:

1. add a large action card area unless business action requires it
2. expose native connections that create incomplete or unsafe records
3. use text blocks that restate table headings

### 4.6 Draft Create Page

Purpose:

Help users complete required fields and save without confusion.

Examples:

1. New Quotation
2. New Sales Order

Do:

1. show draft readiness
2. show save as the primary commit action
3. disable or hide actions that require a saved document
4. keep stock, pricing, and customer warnings as decision support
5. avoid UI flicker while the native form is settling

Do not:

1. make the draft page busier than the form itself
2. show print/email as active before save
3. bypass native validation
4. duplicate native fields in custom panels

### 4.7 Create And Edit Profile Page

Purpose:

Allow controlled maintenance of a business entity.

Examples:

1. Create Customer
2. Edit Customer

Do:

1. limit fields to the approved safe business scope
2. save without surprising navigation
3. stay on the page after save unless the user explicitly navigates
4. center and align form panels
5. distinguish create copy from edit copy
6. explain controlled fields only if users might expect to edit them

Do not:

1. expose credit limits, payment terms, tax settings, or account controls to sales users unless explicitly approved
2. use developer-facing guardrail language
3. leave generic list fallback panels visible
4. create fake saves that do not persist to ERP records

### 4.8 Drill-Down Detail Page

Purpose:

Give a business-friendly view of one entity and its current activity.

Example:

Customer Detail.

Do:

1. support direct URL refresh with the record key in the route
2. show identity, classification, and current posture
3. provide focused filters for activity
4. navigate linked activity through productized routes where possible

Do not:

1. depend only on transient page state
2. send row clicks to generic ERP pages when productized pages exist
3. over-group records if date order is the stronger business need

### 4.9 Guard, Restricted, Empty, And Error Page

Purpose:

Explain why a page cannot show normal content.

Do:

1. identify the condition in business language
2. provide one safe recovery action
3. preserve sidebar and workspace context
4. avoid exposing technical exception details

Do not:

1. show a broken blank page
2. leak stack traces
3. blame the user
4. route automatically to unrelated ERP pages

## 5. Shared Component Standards

### 5.1 Workspace Sidebar

Purpose:

Keep navigation stable across all workspace-owned pages.

Rules:

1. sidebar items are stable destinations, not every card or queue
2. active state must map filtered pages to their parent directory
3. built-in ERP search should be hidden for normal workspace users when scoped search exists
4. utility actions should use the same visual structure as navigation items
5. collapsed state must align icons consistently
6. sidebar header should use business/company language, not project implementation language

Do:

1. keep item height consistent
2. use one active-state design
3. keep search and notification either integrated or visually separated with purpose
4. route through workspace helpers

Do not:

1. show duplicate active items
2. leave native module menu mixed with workspace menu
3. expose `Edit Sidebar` or admin dropdowns to normal sales users
4. use route-specific hacks for active state

Acceptance:

1. page refresh keeps the same sidebar
2. browser back keeps correct active state
3. collapsed sidebar remains aligned
4. no duplicate workspace item appears

### 5.2 Page Shell

Purpose:

Give every page a stable layout foundation.

Rules:

1. content should use a controlled max width unless the table requires full width
2. major cards should align on the same grid
3. do not mix centered and left-aligned cards without purpose
4. top margin and page-head behavior must not cause first-load jumping

Do:

1. use existing shared shells
2. keep page title compact
3. put navigation actions in a consistent place
4. keep body spacing consistent between pages of the same archetype

Do not:

1. create one-off wrapper widths
2. rely on late DOM mutation that visibly moves the page
3. add blank panels to fill space

### 5.3 Summary Cards And KPI Cards

Purpose:

Surface important state quickly.

Rules:

1. card title should be short
2. value should be prominent
3. meta text should explain business meaning only when needed
4. alert borders should indicate real risk, not decoration
5. card counts must match table filters or clearly state their scope

Do:

1. use restrained accent bars or borders
2. keep labels uppercase and compact
3. use currency consistently
4. keep empty or zero values honest

Do not:

1. color every card
2. use warning colors for normal states
3. show metrics the user cannot interpret or act on

### 5.4 Filter Command Strip

Purpose:

Let users change the data view with low effort.

Rules:

1. filter controls and actions must be visually grouped
2. primary filter action order is `Apply`, `Reset`, `Refresh`
3. date filters should use date inputs with calendar affordance
4. a single filter does not need an oversized toolbar
5. labels and values must use consistent meaning

Do:

1. place action buttons close to filters
2. align controls and buttons vertically
3. preserve selected filters in route or payload where useful
4. use "Activity type" when filtering mixed document activity
5. use "Document type" when filtering literal document categories

Do not:

1. put filters on the far left and actions on the far right without a reason
2. use vague labels such as `View` when a clearer business label exists
3. hide Apply below the fold
4. make users hard-refresh to see filter effects

### 5.5 Action Band

Purpose:

Expose the next useful actions without replacing ERP truth.

Semantic families:

1. `commit`: create, save, submit
2. `navigate`: open related pages
3. `communicate`: print, email
4. `collaborate`: assign, comment, share
5. `utility`: refresh, reset, retry, fallback

Rules:

1. one primary action per moment
2. unavailable actions are hidden or disabled with a short reason
3. actions should stay compact when there are only one or two
4. document actions should not become a wall of equal cards
5. native toolbar actions may be orchestrated but not replaced

Do:

1. show Save Draft as primary on drafts
2. keep Print and Email visible on saved documents where business needs them
3. keep Email visible as a future reminder if configuration is pending, but communicate permission/configuration errors safely
4. use follow-up actions only when there is real business value

Do not:

1. show every native menu item in custom UI
2. expose delete or duplicate casually
3. create new downstream documents from Connections unless the business role and route are approved
4. use giant icons or boxed actions that dominate the document

### 5.6 Buttons

Purpose:

Make action hierarchy obvious.

Rules:

1. primary button is dark/navy and reserved for the main action
2. secondary buttons are light and calm
3. navigation-back buttons are compact, soft, and lower emphasis
4. destructive buttons require explicit approval and a separate visual treatment
5. icon-only buttons require accessible labels

Do:

1. keep button height consistent inside a component group
2. align button centers with inputs
3. use hover/focus states that are visible but not loud

Do not:

1. use the same emphasis for Apply and Back
2. make utility buttons look like business commit actions
3. use heavy borders when a soft outline is enough

### 5.7 Data Table

Purpose:

Show records clearly and safely.

Rules:

1. first column should identify the record
2. second-level text should provide useful meta only
3. row open target must be productized if a productized route exists
4. status must be text-visible, not color-only
5. table should support at least the latest 50 records unless the business page intentionally uses a narrower slice

Do:

1. preserve date sorting where recency matters
2. use document-type filtering when mixed activity becomes dense
3. use group-by only when it improves the user's primary task
4. keep row height stable

Do not:

1. use unexplained colored dots
2. hide item names or customer names due to column overflow
3. make the arrow the only clickable area if the row identity should open
4. navigate to raw ERP pages accidentally

### 5.8 Connection Cards

Purpose:

Show meaningful linked records and allowed relationship actions.

Rules:

1. show linked records when they explain the commercial chain
2. hide optional relationship cards with no current business value
3. distinguish group title from child card title visually
4. create actions are allowed only when role, route, and downstream form are approved

Do:

1. use section titles for relationship groups
2. show count chips for linked records
3. route `View linked` to productized pages where available
4. suppress empty optional links unless absence is meaningful

Do not:

1. show `Create new` for delivery, invoice, schedule, or subcontracting records just because ERPNext supports it
2. expose incomplete native forms to sales users
3. make section and child cards look identical

### 5.9 Readiness Checklist

Purpose:

Help users complete drafts.

Rules:

1. each item must represent a required or high-value readiness signal
2. neutral/pending states should be calm
3. warning states should explain risk
4. readiness should not block native save unless ERP validation blocks save

Do:

1. use customer, date, price list, lines, pricing, and stock where relevant
2. show stock availability as decision support, not as a giant panel
3. keep checklist compact above the form

Do not:

1. add readiness items for every field
2. duplicate required-field markers already visible in the form
3. make users fight the checklist before entering data

### 5.10 Create And Edit Form Panel

Purpose:

Support safe maintenance of controlled business profiles.

Rules:

1. use two-column layout when screen width supports it
2. keep title card and form panel the same width
3. center the form stack when it is narrower than the page
4. save should persist to the correct ERP record and linked child records
5. save should not force navigation away unless explicitly requested
6. copy must match create versus edit intent

Do:

1. use a concise title
2. keep the allowed-field note inside the form if needed
3. show save feedback
4. support direct URL reload with record key for edit pages

Do not:

1. leave large unused side space
2. show unrelated result/list panels
3. use gradient backgrounds unless they are part of a clear design system
4. use the same note for create and edit if the user's intent differs

### 5.11 Search

Purpose:

Provide workspace-scoped search that keeps users inside productized routes.

Rules:

1. normal workspace users should use scoped search, not global ERP search
2. search results should prioritize productized workspace pages
3. keyboard shortcut should open only one search experience
4. search dialog text should be concise
5. search must keep working after route transitions

Do:

1. support `Ctrl+K`
2. debounce backend calls
3. show result type and record identity
4. route safely

Do not:

1. open both native and custom search
2. route users to unrelated modules
3. show large explanatory paragraphs in the search dialog

### 5.12 Loading, Skeleton, And First Paint

Purpose:

Avoid visible instability.

Rules:

1. page should not show a native layout and then visibly jump into custom layout
2. placeholder height should match final content as closely as possible
3. mount logic must be idempotent
4. mutation observers must not fight each other
5. data refresh should update content without shaking layout

Do:

1. reserve space for large headers and action bands
2. use stable keys for rerendered content
3. debounce route and mutation sync
4. test hard refresh and back/forward navigation

Do not:

1. repeatedly remove and recreate major DOM regions when a small update is enough
2. let custom sidebar flash between native and productized states
3. depend on manual hard refresh for correct UI

### 5.13 Empty, Blocked, Restricted, And Unavailable States

Purpose:

Explain absence without noise.

Rules:

1. empty state should be specific to the current filter or permission scope
2. blocked state should tell the safe next step
3. restricted state should not reveal hidden record details
4. unavailable route should offer a safe return action

Do:

1. use short business language
2. include one useful action
3. keep visual severity appropriate

Do not:

1. show developer diagnostics
2. expose SQL or server errors
3. blame permissions without explaining what is unavailable

## 6. Business Copy Rules

### 6.1 Copy Intent

Every note must declare one intent:

1. `action`
2. `blocked`
3. `decision`
4. `empty`
5. `exception`
6. `missing`
7. `readonly`
8. `risk`
9. `warning`

If a note does not match one of these intents, remove it.

### 6.2 Preferred Copy Style

Use:

1. short sentences
2. business nouns
3. direct next actions
4. concrete states
5. role-safe wording

Avoid:

1. implementation details
2. apology text
3. training-manual paragraphs
4. generic "please check" text
5. text that exists only to fill space

### 6.3 Good Pattern

Good:

`You can update customer name, group, territory, phone, and email here. Credit limit, payment terms, tax settings, and account controls are managed by Admin or Finance.`

Why:

It tells the business user what is editable and what is controlled elsewhere.

Bad:

`Update safe customer profile fields without leaving Sales Console.`

Why:

It sounds like an implementation note and does not clearly explain the business boundary.

## 7. Route Ownership Standard

### 7.1 Productized Route First

If a productized route exists, all cards, rows, and buttons must use it.

Examples:

1. Customer directory row opens productized Customer Detail
2. Customer Detail activity row opens productized Quotation or Sales Order where available
3. Review Follow-Up opens productized follow-up queue
4. Sales Order linked records use productized worklists or approved native fallback

### 7.2 Native Fallback Is Allowed But Governed

Native fallback is allowed when:

1. no productized route exists
2. the user has valid permission
3. the native page is complete enough for the role
4. the fallback is labeled or intentionally low-emphasis

Native fallback is not allowed when:

1. it exposes unrelated modules
2. it creates incomplete documents
3. it confuses the workspace as source of truth
4. it bypasses approved role boundaries

### 7.3 Deep Link Rule

Any detail, edit, report, or queue page must survive browser refresh.

Required:

1. route key or record key in URL
2. backend can reload context from URL
3. missing key shows a guard state
4. invalid key shows safe unavailable state

Do not depend only on transient JavaScript state.

## 8. Security And Permission Standard

### 8.1 Permission Is Checked Server-Side

Do not rely only on hidden buttons.

Backend methods must verify:

1. doctype permission
2. record permission
3. role-specific operation permission
4. document status rules
5. workflow rules where relevant

### 8.2 Role-Based CUD Rules

Use role-specific boundaries.

Example from Sales Console customer management:

1. Sales User: read customer information
2. Sales Manager: create and update approved profile fields
3. Admin or Finance: credit limit, payment terms, tax, account controls, delete

Delete must remain exceptional.

Do not expose delete because native ERP has it.

### 8.3 Safe Mutation Rules

Any create or update action must:

1. validate input server-side
2. persist to the correct ERP document
3. update linked records intentionally
4. return the saved truth
5. handle duplicate or rename scenarios safely
6. show errors without losing form state

### 8.4 Credential And Secret Rules

Never commit:

1. session IDs
2. API keys
3. passwords
4. cookies
5. production tokens

Smoke tests must use environment variables for secrets.

### 8.5 Output Escaping

Any value rendered into HTML must be escaped unless it is a trusted icon or controlled markup.

Business data must be treated as untrusted:

1. customer names
2. item names
3. comments
4. addresses
5. email fields
6. document references

### 8.6 Audit And Workflow Boundary

The custom UI must not create hidden shortcuts around:

1. approval workflow
2. submit authority
3. cancellation rules
4. document amendment rules
5. stock ledger truth
6. accounting ledger truth

## 9. Stability And Performance Standard

### 9.1 Stability Gates

Every page must pass:

1. hard refresh
2. browser back
3. browser forward
4. sidebar collapse and expand
5. filter apply/reset
6. row open and return
7. saved state reload
8. permission-restricted state

### 9.2 Visual Stability

No page should:

1. flash generic ERP sidebar before custom sidebar longer than necessary
2. show custom and native search together
3. visibly move major panels after first paint
4. duplicate action bands
5. show two selected sidebar items

### 9.3 Runtime Stability

Shared runtimes must be:

1. idempotent
2. route-aware
3. safe to call multiple times
4. tolerant of missing DOM nodes
5. tolerant of permission-limited payloads

### 9.4 Performance Rules

Do:

1. debounce search and route sync
2. avoid repeated full-page rerenders
3. limit default records to a business-safe amount such as latest 50 unless pagination is added
4. avoid expensive backend joins without filters
5. cache static sidebar context where safe

Do not:

1. query every document family on every page load
2. block item/customer entry while background decision-support data loads
3. load all warehouses or all linked history by default

## 10. Accessibility Standard

Every shared component must support:

1. keyboard focus
2. visible focus state
3. non-color status labels
4. meaningful button text or aria label
5. sufficient text contrast
6. readable font sizes
7. no hover-only critical actions
8. reduced-motion safe behavior

Specific rules:

1. icon-only buttons must have labels
2. chips must contain text
3. warning color must be paired with warning text
4. disabled actions must explain why when visible
5. table row actions must be reachable by keyboard

## 11. Visual Design Standard

### 11.1 Layout

Use:

1. consistent max widths by archetype
2. centered form stacks when narrower than page width
3. table width only where data density requires it
4. compact top spacing
5. clear vertical rhythm

Avoid:

1. random panel widths
2. far-separated control groups
3. unused blank cards
4. excessive top helper text

### 11.2 Color

Use color as signal, not decoration.

Preferred posture:

1. navy for primary commit and major hero surfaces
2. white cards with soft borders for normal content
3. teal for positive/ready accents
4. amber for attention
5. red only for real risk or destructive state
6. slate for neutral and metadata

### 11.3 Shadows And Borders

Use:

1. soft card shadows
2. subtle borders
3. selected state with white background and restrained elevation
4. border accents only where business state matters

Avoid:

1. heavy black outlines
2. shadow on every element
3. colored borders for normal information
4. gradient panels unless intentionally part of a page hero

### 11.4 Typography

Rules:

1. title should be direct and compact
2. labels can use uppercase micro-label style
3. values should be stronger than labels
4. helper copy should be smaller and quieter
5. search text should not dominate the sidebar

### 11.5 Design Token Discipline

Shared UI quality depends on reusable visual decisions.

Rules:

1. repeated colors, shadows, radii, spacing, widths, and typography should live in shared component classes or documented tokens
2. new reusable tokens must be semantic, not page-specific
3. page-specific hard-coded values must be rare and justified by business context
4. a new workspace should inherit the existing visual system before inventing new styling
5. one-off visual fixes must not become hidden standards

Do not:

1. copy hex colors between pages without naming their purpose
2. create different button heights for the same action family
3. create unrelated card radius, border, and shadow systems per workspace
4. use gradients or accent colors unless the component role justifies them

### 11.6 Business Data Formatting

ERP UI must format business data consistently.

Rules:

1. money values must clearly show currency when the page compares or commits commercial value
2. date and datetime values must be unambiguous for the user and operating context
3. percentages must identify what they measure
4. quantity precision should match the business decision
5. zero, blank, unavailable, and restricted values must not be visually confused
6. company currency, locale, and ERP formatting helpers should be used where available

Do not:

1. mix date formats on the same workspace
2. mix backend-formatted and frontend-formatted currency without reason
3. round or hide values in a way that changes the user's business decision
4. use placeholder zeros for missing values

## 12. Future Workspace Implementation SOP

Use this sequence for every next workspace.

### Step 1: Define Business Scope

Before code, write:

1. user roles
2. key daily jobs
3. pages needed
4. pages intentionally excluded
5. create/update/delete boundaries
6. native ERP pages that remain acceptable fallback

### Step 2: Map Pages To Archetypes

For each page, assign one archetype:

1. workspace home
2. directory
3. queue
4. report
5. document execution
6. draft create
7. create/edit profile
8. drill-down detail
9. guard/restricted/empty

### Step 3: Reuse Existing Shared Runtime

Choose the shared runtime first:

1. console runtime for workspace home
2. sidebar runtime for managed navigation
3. list shell for directories and queues
4. report shell for analytics
5. child-page shell for document execution
6. form-panel pattern for create/edit profile pages

Only create a new shared runtime when no current runtime fits.

### Step 4: Define Payload Contract

Backend payload must define:

1. title and identity
2. summary cards
3. filters
4. actions
5. rows or sections
6. empty state
7. restricted state
8. route targets
9. permission flags

Do not let frontend guess business truth from raw documents when backend should decide.

### Step 5: Build Route Ownership

Define:

1. route keys
2. active sidebar mapping
3. row open targets
4. back targets
5. native fallback targets
6. unavailable route behavior

### Step 6: Implement Shared Component First

If a new behavior is needed by more than one page:

1. add it to shared runtime
2. document its payload field
3. apply it to the first page
4. apply it to the second page
5. test both

### Step 7: Manual Browser Review

Review:

1. normal width
2. narrow width
3. collapsed sidebar
4. route refresh
5. browser back
6. permission-limited user if available
7. empty data state
8. failed backend state

### Step 8: Freeze And Document

A workspace is not ready for the next big implementation until:

1. code is committed
2. docs match code
3. route ownership is documented
4. page freeze notes are written
5. deferred improvements are listed
6. smoke checks pass

## 13. Forbidden Patterns

These are not allowed in future workspace implementation without explicit approval.

1. page-specific CSS hacks for shared layout problems
2. duplicate sidebar items
3. generic ERP module menu mixed into workspace navigation
4. native global search for normal workspace users when scoped search exists
5. row links that accidentally open raw ERP pages
6. hardcoded session tokens in tests
7. custom saves that do not persist to ERP
8. create buttons for downstream documents that open incomplete native forms
9. helper text that explains implementation instead of business value
10. colored dots without labels
11. large action-card grids for low-value actions
12. hiding permission errors by pretending records do not exist when the user needs a restricted-state explanation
13. adding AI features before the business workflow is stable
14. adding a sidebar `Reports` item before a real report home exists
15. copying Sales Console visual components without copying its route and permission discipline

## 14. Required Acceptance Checklist

Use this checklist before marking any page complete.

### Product Fit

1. page has a clear business purpose
2. target role is known
3. primary action is obvious
4. visible metrics are useful
5. no decorative-only text or cards

### Shared Component Fit

1. page uses the correct archetype
2. shared runtime is used where available
3. new shared behavior is documented
4. no page-local hack solves a shared problem

### Navigation

1. sidebar is stable
2. active item is correct
3. no duplicate selected states
4. browser refresh works
5. browser back and forward work
6. row links use productized routes where available
7. native fallback is intentional

### Actions

1. one primary action per context
2. unavailable actions are hidden or explained
3. save/submit/print/email remain native-truth operations
4. dangerous actions are not casually exposed
5. Back action is low-emphasis and consistently placed

### Data And Permissions

1. backend checks permissions
2. user cannot mutate disallowed fields
3. restricted states are safe
4. no secrets are committed
5. rendered business data is escaped
6. create/update returns saved truth
7. role matrix assumptions are documented for mutation pages

### UI Quality

1. components align
2. filter controls and buttons are grouped
3. no major first-load jump
4. no unnecessary blank space
5. mobile/narrow layout is usable
6. collapsed sidebar is aligned
7. typography hierarchy is clear
8. repeated visual decisions use shared tokens or shared component classes
9. money, date, quantity, and percentage formatting is consistent

### Copy

1. helper text has business intent
2. no implementation language is visible
3. title and filter labels are semantically consistent
4. empty and blocked states are short and helpful

### Validation

1. relevant Python files compile
2. relevant JavaScript files pass syntax check
3. smoke test or manual browser test is recorded
4. docs are updated
5. deferred items are listed, not forgotten

### Final Grade

1. page passes all non-negotiable gates in the implementation contract
2. no unresolved high or medium risk remains
3. route ownership is proven
4. permission and mutation safety are proven where relevant
5. browser verification is recorded
6. docs match code
7. token and business-data formatting discipline is checked
8. the page is safe to use as a future reference pattern

## 15. Sales Console As Current Reference

Sales Console is the current best reference for:

1. stable workspace sidebar
2. scoped workspace search
3. directory versus queue split
4. report shell
5. child document shell
6. action-band grammar
7. customer create/edit safe-field boundary
8. productized customer detail route
9. business copy reduction
10. route guard states

Sales Console is not a reason to copy:

1. page-specific labels without checking business fit
2. sales-only document relationships
3. sales-only role assumptions
4. unfinished deferred features

Future workspaces should inherit the standard, not the accidents of the first implementation.

## 16. Required Companion Documents

This standard must be used with:

1. `enterprise-shared-ui-component-implementation-contract-v1.md`
2. `sales-console-enterprise-readiness-audit-mini-phase-plan.md`
3. `sales-console-enterprise-readiness-sera-0-baseline.md`
4. `sales-console-enterprise-readiness-sera-1-route-ownership.md`
5. future SERA security, stability, and page-family audit notes

The implementation contract is the practical execution gate.

SERA audit notes prove whether the Sales Console reference implementation actually satisfies the standard.

## 17. Next Recommended Audit Work

Continue the page-by-page readiness audit for Sales Console.

The audit should verify:

1. stability
2. route ownership
3. security and permissions
4. UI alignment
5. native fallback boundaries
6. remaining deferred improvements

Only after that audit should a new workspace implementation start.
