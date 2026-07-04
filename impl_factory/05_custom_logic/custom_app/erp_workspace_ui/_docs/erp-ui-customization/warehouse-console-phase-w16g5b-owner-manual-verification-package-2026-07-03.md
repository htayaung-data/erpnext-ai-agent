# Warehouse Console Phase W16G5B Owner Manual Verification Package

Date: 2026-07-03

## Scope

W16G5B is the final source-side owner manual verification audit before any W16H Warehouse Workspace Closure decision. It consolidates what the owner should manually inspect, what Main Control and subagents found, and what remains blocked.

This phase does not approve live alignment, restart, protected gates, commit, push, ERPNext document runtime, stock/accounting mutation, native ERP routes, notification/email/portal behavior, Sales runtime mutation, Procurement runtime mutation, or Warehouse Workspace Closure.

## Decision

W16G5B is not ready for W16H yet.

The Warehouse workspace is broadly active and no longer a planned-shell workspace, but the audit found closure blockers in the newer custom workflow pages. The next phase must be W16G5C before any W16H closure package.

## Current Warehouse Workspace State

The Warehouse workspace now contains active custom workflow and review surfaces:

- Overview command center for navigation and high-level posture.
- Inbound Receiving queue and Receiving Review custom workflow.
- Outbound Picking queue and Picking Review custom workflow.
- Stock Exceptions review routes.
- Returns Work Hub for customer return intake, supplier return candidates, and manager return posture.
- Internal Transfer custom workflow for transfer intent, source count evidence, and manager posture.
- Cycle Count custom workflow for count evidence, variance posture, and manager review.
- Movement Visibility and Transfer Visibility read-only review routes.

The active surfaces remain custom-record-only. ERPNext stock/accounting document execution remains outside this workspace.

## Findings

### High: Existing custom records are not yet reliably reopenable for manager review

Returns, Internal Transfer, and Cycle Count manager posture controls still depend on the custom record id created in the current browser session. After refresh, sign-out/sign-in, or opening the page later, the page does not yet load the persisted custom workflow record and rehydrate manager-review state.

This is not an ERPNext stock/accounting safety issue, but it is a real owner-readiness blocker. A manager must be able to review a saved custom return, transfer candidate, or cycle count task without relying on the same browser session that created it.

Required follow-up: W16G5C should add a clear persisted-record recall/review pattern for Returns, Internal Transfer, and Cycle Count before W16H.

### High: Saveable fake/default evidence values were present in Internal Transfer and Cycle Count

The audit found saveable example values such as fake item codes, generic source references, count-zone text, count notes, and default quantity `1` in Internal Transfer and Cycle Count fields. These could make owner-facing custom records look artificial and could allow users to save placeholder evidence.

W16G5B safe patch response:

- Removed fake/default text and quantity evidence from Internal Transfer candidate fields.
- Removed fake/default text and quantity evidence from Cycle Count task fields.
- Kept controlled select defaults only where they describe an allowed posture/status.
- Updated W9A smoke so tests explicitly enter fixture values before saving, instead of relying on UI defaults.

### Medium: Overview wording overclaimed the available action model

The Overview command section previously said only review routes were available, but several cards now open custom work pages with custom-record save actions. The wording was corrected to say the section opens custom work and review routes.

### Medium: Runtime asset must be included in final staged scope

Receiving and Picking wrappers reference `warehouse_console_theme_patch.js`. At audit time the file is untracked. Before any W16H staged closure package, the runtime asset must either be deliberately included in the Warehouse staged scope or the references must be removed.

### Medium: Dirty worktree must be isolated before closure staging

The working tree still contains unrelated AI assistant files and a Sales smoke audit file. They must remain excluded from Warehouse closure staging unless separately approved.

## Owner Manual Verification Checklist

### 1. Overview Command Center

Owner should confirm after W16G5C:

- The page reads as a command center, not a decorative dashboard.
- Start Warehouse Work opens Inbound Receiving, Outbound Picking, Stock Exceptions, Returns, Internal Transfer, Cycle Count, Movement Visibility, and Transfer Visibility.
- Manager Review cards explain whether they open a review queue or a workflow page.
- Visibility cards are clearly read-only posture/review routes.
- No card says `Planned`, `Shell only`, `Future workflow`, `Preview only`, or `Manager queue`.
- All visible cards either navigate, expose a useful status, or explain an operational purpose.

### 2. Inbound Receiving And Receiving Review

Owner should confirm:

- Inbound Receiving is a usable queue for supplier arrival/count review.
- Receiving Review shows supplier, target warehouse, expected date, and receiving posture clearly.
- Count evidence can be entered and saved only to custom Warehouse Receiving Task records.
- Manager decision controls are disabled for non-manager context and explain why when disabled.
- The page does not create, save, submit, cancel, or amend Purchase Receipt records.
- No stock posting, Stock Ledger, valuation, notification, or native ERP route is exposed.

### 3. Outbound Picking And Picking Review

Owner should confirm:

- Outbound Picking is a usable queue for customer demand and warehouse readiness.
- Picking Review shows customer, warehouse, delivery timing, picking posture, and lines clearly.
- Pick evidence can be entered and saved only to custom Warehouse Picking Task records.
- Manager decision controls are role/state gated and explain why when disabled.
- The page does not create Delivery Note, Pick List, Stock Reservation, Stock Entry, or stock ledger changes.
- No Sales runtime mutation, customer notification, valuation/accounting, or native ERP route is exposed.

### 4. Returns Work Hub

Owner should confirm after W16G5C:

- The dedicated Returns Work Hub is the only active return work surface.
- Customer return intake, supplier return candidate, and return decisions are clear lanes.
- Saved custom return records can be reopened or selected for manager review after page refresh or a new login.
- Forms are aligned, visually calm, and not overloaded with badge clutter.
- Save buttons are consistently placed and visibly tied to the selected lane.
- No Sales Return, Credit Note, Delivery Note, return Purchase Receipt, Purchase Invoice return, debit note, stock movement, notification, email, portal, or native route starts from this hub.

### 5. Internal Transfer

Owner should confirm after W16G5C:

- Internal Transfer reads as transfer intent and source count evidence, not stock transfer execution.
- Candidate evidence fields are understandable and visually consistent with shared Warehouse UI.
- The page does not prefill fake item codes, evidence notes, or quantity evidence.
- Saved custom transfer candidates can be reopened or selected for manager review after page refresh or a new login.
- Manager decisions update only custom candidate status/event posture.
- No Stock Entry, stock movement, reserve/unreserve, Stock Ledger, Stock Balance, Stock Reconciliation, valuation/accounting, notification, or native route starts from this page.

### 6. Cycle Count / Inventory Variance

Owner should confirm after W16G5C:

- Cycle Count reads as count evidence and variance posture, not inventory adjustment execution.
- Count scope, count evidence, variance posture, and manager review are understandable.
- The page does not prefill fake item codes, count-zone text, evidence notes, or quantity evidence.
- Saved custom cycle count tasks can be reopened or selected for manager review after page refresh or a new login.
- Manager decisions update only custom Cycle Count Task status/event posture.
- No Stock Reconciliation, Stock Entry, stock adjustment, Stock Ledger, Stock Balance, Stock Reservation, valuation/accounting, notification, or native route starts from this page.

### 7. Stock Exceptions, Movement Visibility, Transfer Visibility

Owner should confirm:

- Stock Exceptions explains shortage/posture risks and custom review routes.
- Movement Visibility is clearly posted movement evidence review, not document execution.
- Transfer Visibility is clearly posted/inter-warehouse visibility, not internal transfer intent or execution.
- Empty states explain role/scope/source and do not look broken.
- No native ERP document route, valuation/accounting view, stock mutation, or action workflow is exposed.

### 8. Route And Browser Behavior

Owner should confirm after W16G5C:

- Sidebar navigation works on first click without needing a hard refresh.
- Back and Refresh buttons are consistently styled and aligned across Warehouse pages.
- Unsupported or stale Warehouse worklist URLs show a safe unavailable state, not a blank page.
- Browser sign-out/sign-in does not leave stale blank screens for Warehouse routes.

## Validation Performed

Post W16G5B safe patch validation passed:

- `git diff --check HEAD`: passed.
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`: passed.
- `node --check erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`: passed.
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`: passed.
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_theme_patch.js`: passed.
- `python3 -m compileall -q erp_workspace_ui`: passed.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`: passed, 408 tests OK.
- README/W16G5B trailing whitespace check: passed.
- Production saveable fake/default value scan: passed.
- Owner-facing stale wording/native-route scan on production Warehouse JS: passed.
- Cache cleanup/check under `erp_workspace_ui`: clean.

## Boundary Confirmation

W16G5B does not implement or approve Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, return Purchase Receipt, Purchase Invoice return, debit note, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, reserve/unreserve, stock movement, stock posting, valuation/accounting/commercial exposure, notification/email/portal behavior, native ERP document routes, Sales runtime mutation, Procurement runtime mutation, external action, live alignment, restart, protected gate, commit, push, or Warehouse Workspace Closure.

## Next Step

Proceed to W16G5C Custom Workflow Record Recall And Review Persistence.

W16G5C should solve the remaining closure blocker by making saved custom return, internal-transfer, and cycle-count records reopenable or selectable for manager review without relying on same-session DOM state. Only after W16G5C passes source review, smoke coverage, owner manual verification, and dirty-scope containment should W16H Warehouse Workspace Closure be reconsidered.
