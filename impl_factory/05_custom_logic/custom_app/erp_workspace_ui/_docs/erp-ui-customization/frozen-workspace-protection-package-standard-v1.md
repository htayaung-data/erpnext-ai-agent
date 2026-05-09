# Frozen Workspace Protection Package Standard v1

Status: Mandatory project governance standard
Created: 2026-05-07
Owner: ERP UI customization stream
Scope: All ERP Workspace UI workspaces after Sales Console Recovery

Related documents:

- `shared-core-workspace-adapter-contract-v2.md`
- `shared-component-and-implementation-golden-rule-standard-v1.md`
- `native-exception-policy-v1.md`
- `shared-core-route-action-inventory-2026-05-06.md`
- `workspace_governance_manifest.py`

## 1. Purpose

This standard defines the protection package that every workspace must receive before it can be called frozen.

The goal is simple: after a workspace is accepted, future work on Procurement, Warehouse, Finance, Executive, HR, Admin, shared runtime, shared CSS, sidebar, boot routing, report shell, list shell, child-page shell, or another workspace must not silently damage the frozen workspace.

Shared components remain the correct enterprise architecture, but only when frozen workspaces are protected by mandatory regression gates. Without these gates, shared components can create cross-workspace damage. With these gates, shared components become safe, enforceable, and scalable.

## 2. Non-Negotiable Freeze Rule

A workspace is not frozen until it has a complete Frozen Workspace Protection Package.

A future commit is not acceptable if it changes shared core behavior and breaks any frozen workspace protection gate.

A future live alignment is not acceptable if source tests pass but the live frozen workspace protection gate fails.

No agent may say a workspace is frozen based only on unit tests, partial smoke tests, or visual confidence. Freeze requires documented page-by-page evidence.

## 3. Definitions

Frozen Workspace: A workspace that the owner has accepted as enterprise-ready and protected against future regressions.

Protection Package: The complete set of docs, route/action declarations, screenshots, smoke tests, permission tests, native exception evidence, known-risk notes, and mandatory future regression gates for one frozen workspace.

Shared Core: Workspace-wide runtime and design behavior shared across workspaces. This includes shell lifecycle, sidebar, route cleanup, headers, action cards, filters, row links, list shell, report shell, child-page shell, shared CSS, boot routing, and registry behavior.

Workspace Adapter: Workspace-specific business payloads, copy, routes, queues, reports, roles, permissions, and allowed actions.

Governed Native Exception: An approved case where ERPNext native form/report behavior remains transaction truth, but the route/action is declared, permission-gated, visually governed, and smoke-tested.

Protection Gate: The mandatory validation suite that must pass before a frozen workspace can remain accepted after future changes.

Owner Acceptance: Manual owner confirmation after technical validation passes. Technical validation can prove safety; owner acceptance confirms product fit.

## 4. Freeze Lifecycle

Every workspace must pass through these states:

1. Development: Features are still changing.
2. Candidate: Business scope is mostly complete, but final premium UI and regression evidence are not complete.
3. Repair: Final blockers and premium UI defects are being fixed.
4. Acceptance: All gates are run and owner manually checks the workspace.
5. Frozen: Owner accepts the workspace and freeze note is written.
6. Protected: Frozen protection package is complete and mandatory future regression gate is registered.

A workspace is not truly enterprise-frozen until it reaches Protected.

## 5. Required Protection Package Artifacts

Each frozen workspace must include these artifacts.

### 5.1 Final Freeze Note

Required content:

- workspace name
- freeze date
- source branch and commit
- live alignment status
- owner acceptance status
- roles tested
- routes tested
- business scope accepted
- deferred features
- known risks
- native exceptions accepted
- protection gate command list

### 5.2 Final Acceptance Matrix

The workspace must have a page-by-page matrix covering every meaningful route, state, role, and action.

Required columns:

- workspace
- page group
- route
- page archetype
- role tested
- business purpose
- expected shared components
- expected visible actions
- expected hidden/restricted actions
- expected native exceptions
- visual acceptance result
- behavior acceptance result
- security acceptance result
- screenshot artifact
- smoke artifact
- owner note
- status: pass, accepted risk, deferred, or blocker

### 5.3 Route And Action Manifest Coverage

Every visible route and every visible user action must be classified in `workspace_governance_manifest.py`.

Allowed route classifications:

- `productized_overview`
- `productized_worklist`
- `productized_report`
- `productized_detail`
- `managed_create_edit`
- `governed_native_exception`
- `not_allowed_leakage`

Allowed action classifications:

- `productized_navigation`
- `productized_primary_action`
- `productized_secondary_action`
- `governed_native_action`
- `forbidden_mutation`
- `not_allowed_leakage`

No unclassified visible route or action is allowed in a frozen workspace.

### 5.4 Shared Component Mapping

Each workspace must map all pages to the shared component contract.

Required mappings:

- overview shell
- sidebar shell
- page header type
- action card type
- KPI/stat card type
- filter card type
- date-pair layout
- command bar: Apply, Reset, Refresh, Back
- row-link affordance
- table style
- detail header
- detail toolbar
- report shell
- empty/restricted/unavailable/error states
- governed native exception chrome

If a page uses a new component variant, that variant must be named, documented, and approved before freeze.

### 5.5 Baseline Screenshots

Each frozen workspace must have baseline screenshots.

Minimum desktop viewport:

- 1440 x 1100

Recommended additional viewport:

- 1366 x 768 for dense laptop review
- mobile/tablet only if the workspace is intended for those users

Required screenshot categories:

- first login route at early, middle, and ready timing
- direct overview route
- each sidebar route
- each worklist/directory page
- each detail page
- each create/edit page or governed native exception
- each report page
- Apply/Reset/Refresh after-state for representative pages
- autocomplete open state where Link fields exist
- restricted state
- empty state where realistic
- unavailable state where a future-phase route exists
- native exception page after full load
- no-stacking navigation sequence

Screenshots must be stored under a stable artifact folder and referenced from the freeze note.

### 5.6 Smoke Tests

Each frozen workspace must have a frozen protection smoke test.

Minimum smoke coverage:

- login default route lands correctly
- first login is not blank
- direct route load works
- sidebar navigation works
- repeated navigation does not stack shells
- browser back/forward does not duplicate shells or headers
- page refresh reconstructs the correct page
- Overview action cards route correctly
- every visible action is classified in the manifest
- no action silently no-ops
- Apply updates in place
- Reset clears visible filters in place
- Refresh updates in place
- date pairs stay on the same row at desktop width where space allows
- filter buttons are vertically centered with their related filter row
- Link fields show autocomplete suggestions where declared
- focus does not shrink, expand, or shift the page
- productized row links use productized routes first
- no forbidden mutation appears on productized read-only pages
- no raw ERPNext leakage appears except governed native exceptions
- native exceptions keep clean workspace context
- no persistent loading skeleton remains after ready state
- no JavaScript page error occurs
- allowed roles can access the workspace
- restricted roles cannot access direct URLs
- empty/restricted/unavailable/error state kinds are visually distinct

### 5.7 Permission And Security Evidence

The package must prove role safety.

Required checks:

- primary manager role
- primary user role
- restricted same-company role where available
- unrelated workspace role where available
- guest/direct URL behavior
- direct route access for hidden pages
- report access enforcement
- backend permission checks for all payload builders
- no frontend-only permission hiding for sensitive data

### 5.8 Native Exception Evidence

Every governed native exception must have evidence.

Required checks:

- route/action is declared in the manifest
- native exception policy reference exists
- native form/report is only opened intentionally
- productized page remains the primary route where a productized route exists
- native form body can show legitimate ERPNext lifecycle tools
- native tools do not leak into productized read-only pages
- native route keeps workspace sidebar/context where required
- no duplicate native/productized headers
- no persistent managed skeleton after native form is ready

### 5.9 Stability And Latency Evidence

The package must include basic stability evidence.

Required checks:

- first-login route loads useful content without blank state
- no page shaking during ready state
- no visible skeleton remains after load timeout
- no filter focus layout shift
- no page stacking after repeated navigation
- no excessive blank whitespace caused by component layout
- no console JavaScript errors
- no repeated server error response during normal route loading

Recommended checks:

- timing to first useful workspace content
- timing to worklist ready state
- timing to report ready state

### 5.10 Known Risks And Deferred Work

Known risks are allowed only if they are explicit and accepted.

Each known risk must include:

- what remains imperfect
- why it is acceptable now
- user impact
- owner acceptance status
- future phase or repair owner
- whether it blocks future workspace work

Unclear issues cannot be hidden as accepted risk.

## 6. Page Coverage Requirements

A frozen workspace must check every page archetype it owns.

Minimum required page groups:

- login/default landing route
- overview
- sidebar and search shell
- each directory/worklist route
- each priority queue route
- each detail route
- each create/edit route
- each governed native exception route
- each report route
- inquiry/AI assist if the workspace includes it
- empty state
- restricted state
- unavailable state
- error state

For Sales Console, this includes at least:

- Sales Console Home
- Sales Overview
- Quotation Directory
- Sales Order Directory
- Customer Directory
- Customer Detail
- Customer Editor
- Item Directory
- Item Detail
- Sales Order managed detail/new form
- Quotation managed detail/new form
- Delivery Note managed form where exposed
- Sales Invoice managed form where exposed
- Sales Analytics
- Sales Order Analysis
- Trend Analysis
- Collections Status
- Item-wise Sales History
- Inquiry and AI Assist

For Procurement Console, this includes at least the active phase routes at the time of freeze.

## 7. Future Change Protection Rules

Once any workspace is frozen, future work must run protection gates based on file impact.

### 7.1 Always Run All Frozen Workspace Gates When These Areas Change

Run every frozen workspace protection gate if a commit touches:

- shared CSS
- `hooks.py`
- `boot.py`
- workspace registry files
- app boot JS
- sidebar runtime
- route lifecycle runtime
- list page shell
- report page shell
- child/detail page shell
- shared action/card/filter/row-link CSS
- native exception policy
- route/action manifest
- shared component contract docs
- workspace search/global navigation behavior

### 7.2 Run Target Workspace Gate When Adapter Files Change

Run the target workspace protection gate if a commit touches:

- that workspace backend package
- that workspace page controller
- that workspace public JS
- that workspace smoke tests
- that workspace docs

### 7.3 Run Frozen Baseline Gate Before Commit

A commit may proceed only if:

- source tests pass
- changed JS syntax checks pass
- manifest validation passes
- target workspace smoke passes
- every impacted frozen workspace smoke passes
- no new visual difference appears outside the approved change scope

### 7.4 Run Live Gate Before Live Alignment Acceptance

After live alignment, run the same frozen workspace gate against live.

If source passes but live fails, the deployment is not accepted.

## 8. Shared Core Change Safety

Shared Core changes are allowed only when they improve or repair the common platform.

Shared Core changes must not be made to fix one page by silently damaging another workspace.

Before changing Shared Core, the agent must state:

- which shared component is being changed
- which workspaces use it
- which frozen gates will run
- what visual behavior should remain unchanged
- what behavior intentionally changes

Workspace-specific CSS overrides are not allowed when the issue belongs to Shared Core.

A workspace adapter may request a named variant only when the variant is documented and approved.

## 9. Visual Acceptance Rules

The following are blockers for a frozen workspace:

- blank first-login page
- persistent loading skeleton after ready state
- page stacking or duplicate shell/header
- raw native ERPNext leakage from productized pages
- unclassified visible action
- silent no-op action
- forbidden mutation on productized read-only page
- visibly misaligned filter command bar
- date start/end split awkwardly when desktop space allows same-row layout
- action cards forced into a single tall column when grid space exists
- detail header cards floating without a clear information hierarchy
- page shrinking or expanding when a text field receives focus
- autocomplete missing where the field is declared as Link/autocomplete
- implementation-facing copy in normal business UI
- unreadable or crowded table layout that prevents business review
- native form chrome duplicating or fighting managed workspace chrome

Minor visual imperfections can be accepted only if documented as accepted risk.

## 10. Required Protection Gate Commands

Each workspace may define additional commands, but the minimum source gate is:

```bash
python3 -m compileall erp_workspace_ui
PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'
node --check <touched-js-files>
git diff --check
```

Minimum browser gate:

```bash
./run_playwright_docker.sh npm run test:<workspace-frozen-protection>
```

Credentials must be passed through environment variables only.

Agents must not install Node, alter Docker, change Caddy, modify compose files, or change system packages to run browser tests.

## 11. Required File Naming

Recommended artifact and document names:

- `_docs/erp-ui-customization/<workspace>-final-freeze-YYYY-MM-DD.md`
- `_docs/erp-ui-customization/<workspace>-final-acceptance-matrix-YYYY-MM-DD.md`
- `_docs/erp-ui-customization/<workspace>-frozen-protection-package-YYYY-MM-DD.md`
- `ui_smoke/<workspace>_frozen_protection_smoke.js`
- `ui_smoke/artifacts/<workspace>-frozen-baseline-v1/`
- `ui_smoke/artifacts/<workspace>-frozen-protection-latest/`

The freeze note must reference exact artifact paths and commit hashes.

## 12. Future Workspace Implementation Rule

Before starting a new workspace, the agent must read:

- this standard
- the Shared Core + Workspace Adapter contract
- the Golden Rule standard
- the Native Exception policy
- every existing frozen workspace protection package

New workspace implementation must not proceed if current frozen workspace protection gates are failing.

## 13. Future Workspace Freeze Checklist

Before declaring any workspace frozen, answer yes to every item:

- final business scope is accepted
- all active routes are listed
- all visible actions are classified
- shared component mapping is complete
- final acceptance matrix is complete
- desktop baseline screenshots exist
- role and permission tests pass
- direct URL restricted tests pass
- Apply/Reset/Refresh tests pass
- route lifecycle/no-stacking tests pass
- native leakage tests pass
- forbidden mutation scanner passes
- first-login route is not blank
- no persistent skeleton remains
- no console JavaScript errors remain
- owner manually checked the workspace
- freeze note is written
- protection smoke is registered
- future regression gate rule is documented

If any answer is no, the workspace is not frozen.

## 14. How To Modify A Frozen Workspace

A frozen workspace may be modified only through a controlled recovery or enhancement phase.

Required process:

1. State why the frozen workspace must change.
2. Capture before screenshots.
3. Identify affected shared components and adapter files.
4. Update contract or manifest if behavior changes.
5. Implement in Sequential Exit-Gate Mode.
6. Run the frozen workspace protection gate.
7. Run all other impacted frozen workspace gates if Shared Core changed.
8. Capture after screenshots.
9. Update freeze/recovery documentation.
10. Obtain owner acceptance if visual or behavior changes are user-visible.

Silent changes to frozen workspace behavior are not allowed.

## 15. Failure Handling

If a frozen protection gate fails:

- stop the phase
- do not commit unless the failure is an explicitly documented unrelated pre-existing issue and owner grants a waiver
- classify the failure as blocker, accepted risk, or deferred
- if shared core changed, identify all impacted workspaces
- repair or revert the offending change
- rerun the gate

Waivers must be rare. A waiver must include:

- exact failed test
- why it is unrelated
- why it is safe to proceed
- future owner/phase to fix it
- owner approval

## 16. Enterprise Acceptance Principle

The standard for frozen workspaces is enterprise product quality, not MVP quality.

A page can pass technical tests and still fail freeze if it looks childish, unstable, misaligned, confusing, or inconsistent with the shared design system.

Manual visual acceptance is therefore mandatory. Automated gates protect against regression, but owner and senior UI review decide final premium readiness.
