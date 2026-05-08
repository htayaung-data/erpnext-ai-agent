# Shared Core and Workspace Adapter Contract v2

Date: 2026-05-06
Status: Mandatory Main Phase 1 governance contract
Applies to: Sales Console, Procurement Console, and every future ERP workspace
Supersedes for implementation planning: the workspace-specific interpretation of the v1 shared component docs where they are less strict or imply page copying.
Keeps as historical references: `shared-component-and-implementation-golden-rule-standard-v1.md`, `enterprise-shared-ui-component-standard-v1.md`, `enterprise-shared-ui-component-implementation-contract-v1.md`, and workspace freeze/phase notes.

## 1. Purpose

This v2 contract separates the ERP Workspace UI platform into two layers:

1. Core Shared System
2. Workspace Adapter

Future implementation must begin from Core + Adapter. Agents must not copy Sales Console page files, Procurement Console page files, old screenshots, or workspace-specific CSS as the starting architecture for a new page or workspace.

Sales Console remains the frozen business reference. Procurement Console is the current Phase 3 buyer workbench. Neither workspace is the shared core by itself.

## 2. Source Of Truth Order

Use this order when the current code, docs, screenshots, or implementation opinions disagree:

1. ERPNext permission, workflow, accounting, stock, and document lifecycle truth
2. current clean source repo on `feature/erpnext-ui-design`
3. route/action manifest and native exception policy
4. this Core + Adapter v2 contract
5. Golden Rule v1 and enterprise shared component v1 docs
6. Sales freeze and Procurement phase notes
7. screenshots, artifacts, and older discovery notes

The live deployment repo is not the source of truth for this phase. It is a deployment and integration working tree until live alignment is explicitly approved.

## 3. Core Shared System Responsibilities

The Core owns visual and behavioral rules that must remain consistent across workspaces.

### 3.1 Shell Lifecycle

Core owns first paint, skeleton/guard rendering, ready-state replacement, refresh behavior, and teardown.

Core must ensure:

1. a page does not flash unrelated native content before the managed shell is ready
2. a loading shell cannot remove a newer ready shell
3. refresh and route re-entry replace stale shell state instead of stacking content
4. guarded states render through the same shell family as ready states

Workspace adapters provide payloads and route identity. They do not own shell lifecycle mechanics.

### 3.2 Route Cleanup And No-Stacking

Core owns route cleanup, detached wrapper removal, duplicate shell prevention, and stale previous-content removal.

Every managed route must satisfy:

1. one visible workspace shell for the active route
2. no stale Overview, Worklist, Report, Detail, or native parent header left behind after navigation
3. back/forward route changes do not duplicate managed shells
4. direct refresh reconstructs the same route from URL and backend payload, not from transient JavaScript state alone

### 3.3 Sidebar Behavior

Core owns sidebar shell, workspace header, active-item rendering, collapse behavior, search entry point, and native sidebar suppression on managed workspace routes.

Adapters own sidebar destinations, labels, counts, route targets, role visibility, and active-key mapping.

Core must not show native ERP module menus mixed into normal workspace navigation.

### 3.4 Page Header And Breadcrumb Discipline

Core owns header hierarchy, density, breadcrumb slots, title scale, chip style, and header action layout.

Adapters own business words inside those slots.

Rules:

1. headers must show the workspace/business route identity, not generic route names such as `Procurement Console Worklist`
2. breadcrumbs must use productized workspace parents before native ERP parents
3. managed native exceptions must keep clean workspace chrome and avoid duplicate native/productized headers
4. detail/review pages use compact headers, not overview hero/action-card styling

### 3.5 Overview Hero/Header

Core owns overview layout, priority card grid, action-card style, metric style, spacing, responsive behavior, and no-stacking lifecycle.

Adapters own overview sections, business metrics, action targets, and business copy.

Overview pages must be useful workbenches, not raw DocType launchers.

### 3.6 Action Cards And Toolbars

Core owns action hierarchy and component shapes:

1. overview action cards
2. compact detail toolbar buttons
3. worklist/report command-strip buttons
4. disabled, restricted, empty, loading, and error states

Adapters own which actions are allowed.

Adapters must not introduce one-off visual action styles unless the variant is named in this contract or a future approved variant document.

### 3.7 List/Worklist Shell

Core owns worklist/list shell rendering:

1. summary area
2. filters and command strip
3. result table
4. row action affordance
5. empty/restricted/unavailable/error rendering
6. in-place Apply/Reset/Refresh behavior
7. link/autocomplete control behavior
8. responsive table and filter layout

Adapters own queue keys, filters, columns, rows, row target mapping, permissions, and state payloads.

Directory and worklist headers that expose metrics must use the Core-owned premium header structure:

1. title and description render first as the clear header copy row
2. KPI or metric cards render below that copy as a full-width grid inside the same header component
3. metric cards use shared min/max sizing, shared minimum height, consistent gaps, border treatment, accent treatment, typography, and internal padding
4. three-card sets use the approved centered fixed-width grid so sparse metric sets do not appear right-aligned or accidental
5. four-card sets use equal-width four-column tracks across the available header width
6. five-card sets use equal-width five-column tracks across the available header width
7. all count variants must avoid clipped text, cramped labels, and accidental wrapping at desktop widths

Adapters own the metric labels, values, tone, and business meaning, but not the metric-card layout.

### 3.8 Filter Panel

Core owns filter field spacing, label placement, link-field display, autocomplete behavior, command alignment, and keyboard/focus posture.

Adapters own filter definitions, field names, DocType targets for link fields, defaults, and safe filter coercion.

The shared filter width contract is:

1. standard fields use controlled equal-width tracks
2. date-window fields use the shared date-width track and stay paired when space allows
3. keyword, search, text, and link lookup fields use the flexible track after standard/date fields are governed
4. flexible search fields must keep the Core-defined minimum width and must not be squeezed by contextual create actions
5. Apply, Reset, Refresh, Back, and contextual create actions render as one compact command group
6. when the filter row cannot keep a premium gap before the action group, the action group moves to a clean right-aligned action row instead of crowding the last field
7. focus, autocomplete, and refresh states must not resize the page, shift the command group, or overlap controls

No workspace may use a page-local filter layout to bypass the shared shell unless the Core gains a named variant first.

### 3.9 Date-Pair Rule

Core owns date-pair layout.

Date From and Date To fields for the same business window must stay on the same row at desktop widths when space allows. They may stack responsively on narrower widths. This rule applies to Sales reports, Procurement worklists, Procurement reports, and future date-window surfaces.

Adapters own the business meaning of the date window.

### 3.10 Apply, Reset, Refresh AJAX Behavior

Core owns command behavior:

1. Apply updates the active content area in place
2. Reset clears visible controls and then reloads data in place
3. Refresh reloads the current payload in place
4. these commands must not force native query-string reloads unless ERPNext native form lifecycle requires it

Adapters own the backend method and filter payload shape.

### 3.11 Row-Link And Table Action Style

Core owns row-link affordance style, table action placement, focus state, hover state, and accessible label behavior.

Adapters own target classification and route payload.

Rows on productized pages must prefer productized routes. Direct native form routes are allowed only as governed native secondary actions declared in the manifest and native exception policy.

### 3.12 Detail/Review Child Shell

Core owns compact detail/review shell structure:

1. compact header
2. toolbar row
3. facts and chips
4. sections and tables
5. downstream visibility sections
6. guarded states
7. no stale parent shell after navigation

Adapters own entity payloads, section content, row targets, role/scope checks, and read-only versus mutation posture.

### 3.13 Compact Detail Toolbar

Core owns compact toolbar styling and hierarchy. Back, Refresh, and governed native-form actions must render as compact toolbar controls on detail/review pages.

Adapters own whether the governed native-form action exists. If present, it must be secondary, permission-gated, and declared in the manifest.

### 3.14 Report Shell

Core owns report shell layout:

1. summary/header
2. command strip
3. filter panel
4. metrics
5. chart/table region
6. empty/restricted/unavailable/error states
7. in-place Apply/Reset/Refresh behavior

Adapters own report keys, report builder methods, native report wrappers, filters, columns, rows, metrics, and business copy.

Report filters follow the same shared width and action alignment contract as list/worklist filters. The last report filter field must keep a clear visual gap before Apply. If a report row has too many standard filters for a premium single-line layout, the action group moves to a clean right-aligned action row instead of touching, covering, or crowding the final field.

Wide report tables must remain contained inside the report card: horizontal overflow belongs to the table wrapper, not the page viewport. Numeric columns should be right-aligned with tabular numerals and should not wrap awkwardly. Wide financial or month-based tables may use an intentional horizontal scroll region, with the first important column kept readable when the Core renderer supports it.

These directory metric, filter width, report spacing, and wide-table containment rules apply to Sales, Procurement, and all future Core + Adapter workspaces.

### 3.15 State Kinds

Core recognizes these state kinds only:

1. `ready`
2. `empty`
3. `restricted`
4. `unavailable`
5. `error`

Adapters must map business truth into these state kinds. Permission failures are `restricted`, missing future features are `unavailable`, valid zero-result payloads are `empty`, and technical failures are `error`.

### 3.16 Native Exception Wrapper And Chrome

Core owns native exception chrome:

1. workspace sidebar remains present where the workspace launched the native form
2. breadcrumb/header identify the workspace and business parent
3. native ERP form body remains transaction truth
4. duplicate headers and stale productized content are removed
5. browser refresh reconstructs the intended workspace context where possible

Adapters own which native exceptions are allowed and the route/action manifest entries for them.

### 3.17 Copy Language Rules

Core owns copy boundaries:

1. no method names, framework words, route keys, or internal implementation language in normal user copy
2. compact, business-useful helper text only
3. restricted/unavailable copy must be calm and specific
4. implementation terms such as `native ERP` should appear only when explaining a governed exception to an authorized operator, not as routine page language

Adapters own business vocabulary, domain labels, and role-specific phrasing.

### 3.18 Accessibility And Focus Behavior

Core owns:

1. keyboard focus order inside command strips and tables
2. visible focus states
3. focus stability when filters open autocomplete menus
4. accessible labels for icon or compact controls
5. no layout jump during focus/blur

Adapters own field labels, option labels, and action labels.

### 3.19 Responsive Layout

Core owns responsive breakpoints and stable layout behavior across overview, worklist, report, and detail shells.

Adapters must not solve responsive issues by adding page-local CSS that changes shared component contracts. If an adapter exposes a real domain need, the Core must gain or approve a named variant.

### 3.20 Browser Smoke Expectations

Core-owned browser smoke expectations:

1. direct route load
2. refresh
3. back/forward
4. Apply/Reset/Refresh command behavior
5. no duplicate managed shell
6. no native sidebar/header leakage on managed routes
7. date-pair and filter layout stability
8. row-link target classification
9. governed native exception chrome lifecycle
10. restricted and unavailable states

Adapters own role credentials, domain seed records, expected queue/report keys, and business assertions.

## 4. Workspace Adapter Responsibilities

Adapters translate one business workspace into Core payloads and approved route/action declarations.

Adapters own:

1. business vocabulary
2. route keys and route patterns
3. backend method ownership
4. domain payload fields
5. role and scope rules
6. allowed actions
7. governed native exceptions
8. worklist/report/detail business content
9. state-kind mapping
10. smoke data and role matrix expectations

Adapters must not own shared visual behavior, shell lifecycle, no-stacking cleanup, filter layout, date-pair layout, row-link style, action-card style, or report shell layout.

## 5. Adapter Override Rule

Workspace adapters must not override Core visual or behavioral rules unless all of the following are true:

1. the variant has a stable name
2. the variant is documented in this contract or an approved addendum
3. the route/action manifest declares where it is used
4. at least one cross-workspace impact is assessed
5. tests or smoke expectations cover the variant

Unapproved page-local hacks are contract violations even when the page appears visually acceptable.

## 6. Current Workspace Application

### Sales Console

Sales Console is frozen as the business reference and remains status `frozen` in the registry.

Main Phase 2 Sales Recovery on 2026-05-06 hardens Sales against this v2 Core + Adapter contract without renaming frozen routes or changing confirmed Sales business scope. Future Sales changes must continue to preserve the freeze baseline unless the owner explicitly approves a new recovery phase.

Sales managed document forms for Quotation, Sales Order, Delivery Note, and Sales Invoice are classified as managed create/edit surfaces where ERPNext remains transaction truth.

### Procurement Console

Procurement Console is Phase 3 and Purchase-role home routing is owner-approved.

Main Phase 1 does not repair Procurement UI, add Procurement Phase 4, or add new Procurement mutation features. Later Procurement Recovery work must repair or harden Procurement against this v2 Core + Adapter contract.

Procurement native PR/RFQ/Supplier Quotation/Purchase Order create forms remain governed native exceptions until a future owner-approved Managed Procurement Forms phase replaces them.

## 7. Future Workspace Startup Rule

Every future workspace must start by:

1. adding or updating route/action manifest entries
2. declaring Core shell usage
3. declaring adapter-owned business payload fields
4. declaring role/scope rules
5. declaring governed native exceptions, if any
6. adding contract tests
7. using shared Core shells before adding page-specific code

Do not create a future workspace by copying Sales Console or Procurement Console page files and renaming labels.

## 8. Completion Gate For Shared-Core Changes

Any shared Core change must record:

1. affected shell family
2. affected workspace adapters
3. manifest impact
4. tests run
5. browser smoke impact
6. docs updated if the contract changes

A shared Core change is a product change, not a local styling tweak.
