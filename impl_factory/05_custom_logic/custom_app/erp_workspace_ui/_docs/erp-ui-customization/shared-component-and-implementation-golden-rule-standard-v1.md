# Shared Component and Implementation Golden Rule Standard v1

Date: 2026-05-03
Status: Mandatory workspace-wide UI governance standard
Scope: all ERP workspace UI pages, shared components, managed ERP form overlays, reports, directories, details, and future workspaces
Reference implementation: Sales Console final freeze package
Detailed parent standard: `enterprise-shared-ui-component-standard-v1.md`
Execution contract: `enterprise-shared-ui-component-implementation-contract-v1.md`

## 1. Purpose

This is the first document every future ERP workspace implementation must read.

It is intentionally not named after Sales Console.

Sales Console is the current reference implementation because it is the first workspace to pass the strongest review cycle. It is not the product scope for every future workspace.

Future workspaces must copy the operating rules, not the Sales Console page content.

The Golden Rule is:

`Shared component first, ERP truth always, business purpose before decoration, evidence before freeze.`

## 2. Source Of Truth Chain

When there is disagreement, use this order:

1. current code in the clean UI branch
2. ERPNext permission, workflow, status, accounting, and stock truth
3. this Golden Rule standard
4. `enterprise-shared-ui-component-standard-v1.md`
5. `enterprise-shared-ui-component-implementation-contract-v1.md`
6. workspace-specific freeze notes and SERA audit notes
7. screenshots and manual opinions

Screenshots are useful for visual review, but screenshots do not override route safety, permission safety, shared component rules, or backend business truth.

## 3. Non-Negotiable Golden Rules

### Rule 1: Business Purpose Before UI

Do not create a page because a DocType, report, or empty screen area exists.

Every page must answer:

1. who uses it
2. what decision or action it supports
3. what it intentionally does not do
4. what native ERP page remains the transaction source of truth

### Rule 2: Shared Shell Before Page Layout

Choose the shared shell before designing the page.

Default shell choices:

1. workspace home: console runtime
2. directory and queue: list page shell
3. report: report page shell
4. saved document: child page shell on managed ERP form
5. draft create: child page draft readiness pattern on managed ERP form
6. create/edit profile: governed form-panel pattern
7. drill-down detail: worklist detail pattern
8. blocked, empty, restricted, unavailable: shared guarded state pattern

If no shell fits, extend the shared runtime first. Do not create a page-local copy of a reusable component.

### Rule 3: Declare The Archetype Before Coding

Every page must declare one primary archetype:

1. workspace home
2. directory
3. queue
4. report
5. managed document execution
6. draft create
7. create/edit profile
8. drill-down detail
9. guard, restricted, empty, or unavailable state

If one screen appears to need many archetypes, split it or make the primary and secondary sections explicit.

### Rule 4: Backend Owns Business Truth

The frontend renders business decisions. The backend decides business truth.

Backend payloads must provide:

1. page identity
2. role and permission flags
3. route keys
4. filter definitions
5. metrics and cards
6. rows, sections, or chart data
7. allowed actions
8. empty, blocked, restricted, or unavailable states
9. saved truth after mutation

Frontend code must not infer permission, workflow, credit, stock, accounting, or ownership truth from raw DOM state.

### Rule 5: Productized Route First

If a productized route exists, use it for cards, rows, search results, breadcrumbs, buttons, and back links.

Route targets must be classified as:

1. productized route
2. managed native form
3. governed native fallback
4. deferred route notice
5. blocked route

Raw native ERP routes are not automatically acceptable.

### Rule 6: One Active Navigation Truth

Every workspace must keep navigation stable:

1. one selected sidebar item only
2. detail and editor routes highlight their parent destination
3. managed document forms highlight their business family
4. report routes follow an approved report navigation rule
5. native ERP module menus do not mix into normal workspace navigation

### Rule 7: In-Place Interaction By Default

Apply, Reset, Refresh, search, table reload, and report reload should update the relevant content area without forcing a full page reload.

Full reload is acceptable only when:

1. ERPNext native form lifecycle requires it
2. route identity changes
3. a safe recovery path is needed after an unrecoverable client state

Reset must reset both visible controls and the resulting data.

### Rule 8: Premium Means Stable And Useful

Premium UI is not more decoration.

Premium UI means:

1. first paint does not shake or jump
2. action hierarchy is obvious
3. filters and buttons align as one command strip
4. cards have enough breathing room
5. values are formatted for business reading
6. helper text is short and useful
7. empty and restricted states are calm and clear
8. the page survives refresh, back, forward, and narrow widths

### Rule 9: Business Copy Must Earn Its Space

Do not expose implementation language to normal users.

Avoid phrases such as:

1. method names
2. agent names
3. internal route keys
4. framework words
5. long explanations that repeat what the screen already shows

Use copy that explains business meaning, risk, next step, or safe limitation.

### Rule 10: Permission-Safe Mutation Only

Create, update, delete, submit, cancel, workflow, and save actions must be checked server-side.

Required checks:

1. role
2. doctype permission
3. record permission
4. field allowlist
5. document status or workflow state
6. scope ownership where applicable
7. safe error response that does not lose user input

Delete is exceptional and must not appear by default.

### Rule 11: Evidence Before Freeze

No page is frozen because it looks acceptable in one browser screenshot.

Freeze evidence must include:

1. relevant Python compile check
2. relevant JavaScript syntax check
3. unit or contract tests where available
4. browser verification for normal route, refresh, back, and filter behavior
5. role and permission verification where relevant
6. docs updated to match code
7. deferred items listed clearly

### Rule 12: Shared Component Changes Must Be Treated As Product Changes

Changing a shared component affects future workspaces.

Before changing shared runtime or shared CSS:

1. identify every page family likely affected
2. keep the existing payload contract backward compatible when possible
3. update the parent standard or implementation contract if behavior changes
4. test at least one current consumer
5. document the reason and accepted risk

### Rule 13: Workspace Registry Before New Workspace

Every workspace must be declared in the workspace registry before its routes, sidebar, search, worklists, reports, or app boot behavior are exposed.

Required registry decisions:

1. matrix name
2. recommended enterprise name when different
3. route ownership
4. backend method ownership
5. role family
6. managed doctypes
7. sidebar active-key mapping
8. freeze or planned status

Sales Console route names are frozen. Do not rename Sales Console to make the first workspace look generic. Map future workspaces through the registry instead.

## 4. Current Shared Runtime Map

The current reusable implementation lives in:

1. `erp_workspace_ui/workspace_registry.py`
2. `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
3. `erp_workspace_ui/public/js/runtime/console/workspace_console_runtime.js`
4. `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`
5. `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
6. `erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js`
7. `erp_workspace_ui/public/js/runtime/child_page/child_page_shell.js`
8. `erp_workspace_ui/public/js/runtime/child_page/child_page_shell_content.js`
9. `erp_workspace_ui/public/js/runtime/child_page/child_page_connections.js`
10. `erp_workspace_ui/public/js/runtime/child_page/child_page_details.js`
11. `erp_workspace_ui/public/js/runtime/child_page/child_page_sections.js`
12. `erp_workspace_ui/public/js/runtime/child_page/child_page_helpers.js`
13. `erp_workspace_ui/public/css/erp_workspace_ui.css`

The shared CSS prefix is `erpw-`.

The shared token prefix is `--erpw-`.

New repeated UI behavior must be implemented through these shared assets or through a documented new shared runtime.

## 5. Required Implementation Sequence

Use this order for every new workspace or major page family:

1. write the business scope
2. list user roles
3. list pages intentionally included and excluded
4. confirm matrix name versus recommended enterprise name
5. declare the workspace registry definition
6. map every page to an archetype
7. choose the shared shell for every page
8. define route ownership and active navigation mapping
9. define backend payload contracts
10. define role and permission boundaries
11. implement shared behavior first
12. implement page-specific business logic second
13. run syntax, unit, browser, and permission checks
14. update docs and tests before freeze

If any item is unknown, stop and resolve it before broad implementation.

## 6. Required Page Contract

Every page must document:

1. route
2. page archetype
3. target role
4. shared shell
5. backend method or native source
6. primary action
7. secondary actions
8. allowed native fallback
9. restricted state behavior
10. empty state behavior
11. filter behavior
12. browser refresh behavior
13. permission and mutation boundary
14. tests or browser verification evidence

## 7. Hard No-Go Patterns

These are blocked unless a documented waiver is approved:

1. page-local CSS for a shared alignment problem
2. one-off buttons that duplicate shared action grammar
3. full page reload for Apply, Reset, or Refresh when the shell supports in-place reload
4. raw ERP route leakage when a productized route exists
5. create or edit action without server-side permission checks
6. helper text that explains implementation instead of business meaning
7. dashboard pages that duplicate existing reports without distinct decision value
8. AI features before the core workflow is stable
9. hardcoded credentials, session IDs, or secrets in docs, tests, or code
10. changing shared CSS tokens to satisfy one page without checking consumers

## 8. Waiver Rule

Waivers must be rare.

Every waiver must record:

1. rule waived
2. page or component affected
3. business reason
4. risk
5. compensating control
6. owner
7. review date or removal condition

Waivers are not allowed for speed alone, visual preference alone, or avoiding shared component work.

## 9. Future Agent Prompt Requirement

Any future AI agent or developer prompt for another workspace must include this paragraph:

`Follow the Shared Component and Implementation Golden Rule Standard. Start from shared runtime and documented archetypes. Do not create page-local hacks for shared layout or behavior. Do not expose raw ERP routes when productized routes exist. Do not add mutation actions without server-side permission checks. Update tests and docs to match the final code before freeze.`

## 10. Freeze Definition

A workspace is ready to freeze only when:

1. every page has a declared archetype
2. every repeated UI pattern uses or extends a shared component
3. every route has an ownership classification
4. every mutation is permission-safe
5. browser route, refresh, back, and filter behavior are verified
6. role restrictions are verified
7. docs match code
8. deferred items are explicit and accepted
9. no unresolved high or medium risk remains

If those conditions are not true, the workspace can be useful, but it is not a Golden Rule reference.
