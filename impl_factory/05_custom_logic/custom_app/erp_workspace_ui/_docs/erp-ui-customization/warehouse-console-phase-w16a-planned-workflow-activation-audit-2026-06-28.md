# Warehouse Console Phase W16A Planned Workflow Activation Audit

Date: 2026-06-28
Status: Docs-only activation audit and real workspace-closure roadmap
Owner: ERP UI Main Agent
Review mode: Hybrid Review Ladder before implementation, separate review agents for major runtime activation

## 1. Purpose

W15J closed and pushed the Warehouse workflow foundation milestone. It did not close the Warehouse workspace.

True Warehouse Workspace Closure means the owner-facing Warehouse Overview must not leave business-critical work as unresolved `Planned`, `Shell only`, or inert preview controls. W16 starts the work of turning those planned areas into real custom workflow behavior one by one.

This document defines the remaining planned inventory, safe activation order, blocked ERPNext document boundaries, and the minimum closure bar before the Warehouse workspace can be called complete.

## 2. Non-Goals

W16A does not implement runtime behavior.

W16A does not approve:
- Purchase Receipt draft/create/save/submit/cancel/amend.
- Delivery Note, Pick List, or Stock Reservation runtime.
- Sales Return, Credit Note, Purchase Invoice return, debit note, or supplier notification.
- Stock Entry draft/create/save/submit/cancel/amend.
- Stock Reconciliation draft/create/save/submit/cancel/amend.
- Stock Ledger, Stock Balance, or Stock Reservation mutation.
- Stock movement, stock posting, valuation, accounting, commercial amount, payable, receivable, GL, tax, landed cost, margin, payment, or billing exposure.
- native ERPNext route exposure such as `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report`.
- Email, portal, customer notification, supplier notification, or external action.
- Sales, Procurement, Finance/Admin, or Inventory/Admin runtime mutation from Warehouse Console.
- Live alignment, restart, protected gate, or release closure.

## 3. Current Foundation After W15J

The following custom-record foundations exist and are hardened enough to be candidates for controlled UI activation:

| Area | Existing backend foundation | Current owner-facing state |
| --- | --- | --- |
| Inbound receiving | `save_warehouse_receiving_task_draft`, `save_warehouse_receiving_manager_decision` | Detail page shell controls are inert |
| Outbound picking | `save_warehouse_picking_task_draft`, `save_warehouse_picking_manager_decision`, `request_warehouse_dispatch_handoff` | Detail page shell controls are inert |
| Customer return | `save_warehouse_customer_return_intake_draft`, `save_warehouse_customer_return_manager_decision`, `request_warehouse_customer_return_handoff` | Overview planned lane only |
| Supplier return | `save_warehouse_supplier_return_candidate_draft`, `save_warehouse_supplier_return_manager_decision`, `request_warehouse_supplier_return_handoff` | Overview planned lane only |
| Internal transfer | `save_warehouse_internal_transfer_candidate_draft`, `save_warehouse_internal_transfer_manager_decision`, `request_warehouse_internal_transfer_handoff` | Overview planned lane only |
| Cycle count / inventory variance | `save_warehouse_cycle_count_task_draft`, `save_warehouse_cycle_count_manager_decision`, `request_warehouse_inventory_variance_handoff` | Overview planned lane only |

All of these foundations are custom Warehouse records only. They must remain separated from ERPNext stock/accounting document execution unless a later owner/security-approved phase explicitly changes that boundary.

## 4. Remaining Planned Inventory

### 4.1 Warehouse Overview Action Center

The Action Center still has planned cards:

| Card | Current state | Required real behavior before closure |
| --- | --- | --- |
| Return intake | Planned | Route to active customer/supplier return intake queues or an active Returns work hub backed by custom return records |
| Cycle counts | Planned | Route to active cycle count task queue backed by custom cycle count records |
| Return decisions | Planned | Route to active manager decision queue for customer/supplier return records |
| Inventory variance | Planned | Route to active variance review and Inventory/Admin request queue backed by custom cycle count and variance handoff records |

### 4.2 Compact Planned Workflow Shells

The Overview planned workflow shell section still has four lanes:

| Lane | Current state | Required real behavior before closure |
| --- | --- | --- |
| Customer return intake | Shell only / request only | Active custom-record intake, manager decision, and Sales/Finance handoff request UI |
| Supplier return candidate | Shell only / request only | Active custom-record candidate, manager decision, and Procurement/Finance handoff request UI |
| Internal transfer candidate | Shell only / request only | Active custom-record transfer intent, manager decision, and Inventory/Admin handoff request UI |
| Cycle count / inventory variance | Shell only / request only | Active custom-record count task, manager variance decision, and Inventory/Admin handoff request UI |

### 4.3 Receiving Detail Page

The Receiving Review detail page still shows shell-only planned controls even though backend methods exist.

Required before closure:
- Warehouse user can save receiving count evidence to custom `Warehouse Receiving Task` only.
- Warehouse user can send the task to manager review.
- Warehouse manager can record approved receiving posture, discrepancy posture, recheck request, or Procurement escalation posture.
- Purchase Receipt remains blocked unless a separate policy phase approves it.

### 4.4 Picking Detail Page

The Picking Review detail page still shows shell-only planned controls even though backend methods exist.

Required before closure:
- Warehouse user can save pick evidence to custom `Warehouse Picking Task` only.
- Warehouse user can send the task to manager review.
- Warehouse manager can record clean pick, partial/shortage posture, repick request, Sales escalation, or dispatch handoff posture.
- Dispatch handoff remains request-only custom record behavior.
- Delivery Note, Pick List, Stock Reservation, and stock posting remain blocked unless separate policy phases approve them.

## 5. Recommended W16 Implementation Sequence

The sequence should activate lower-risk custom workflows first and defer ERPNext document runtime.

### W16B - Activate Inbound Receiving Custom Workflow UI

Goal: remove shell-only behavior from receiving detail controls.

Scope:
- Add UI controls for count evidence draft and manager decision using existing custom backend methods.
- Add request-id/idempotency handling in UI.
- Add owner-facing status labels and safe success/error feedback.
- Keep Purchase Receipt blocked.

Why first:
- Backend exists.
- Business flow is foundational.
- It affects the existing live receiving review route, not a new cross-role workspace.

### W16C - Activate Outbound Picking Custom Workflow UI

Goal: remove shell-only behavior from picking detail controls.

Scope:
- Add UI controls for pick evidence draft, manager decision, and request-only dispatch handoff using existing custom backend methods.
- Keep Delivery Note, Pick List, Stock Reservation, and stock posting blocked.

Why second:
- Backend exists.
- Outbound fulfillment is a high-value operational lane.
- Dispatch handoff is request-only and already bounded.

### W16D - Activate Returns Work Hub Foundation

Goal: replace the single planned `Return intake` and `Return decisions` Action Center cards with useful custom workflow entry points.

Scope:
- Decide whether Overview shows one Returns hub or two separate cards: Customer Return and Supplier Return.
- Recommendation: one compact Returns hub in Overview, with two tabs or lanes inside the hub.
- Activate custom-record customer return and supplier return intake/candidate queues.
- Keep Sales/Finance/Procurement/Admin handoffs request-only.
- Keep Sales Return, Credit Note, Purchase Invoice return, debit note, supplier notification, customer notification, and stock mutation blocked.

### W16E - Activate Internal Transfer Candidate Workflow UI

Goal: replace `Internal transfer candidate` planned lane with active custom-record transfer intent and review UI.

Scope:
- Add custom transfer candidate entry, manager decision, and Inventory/Admin handoff request UI.
- Keep Stock Entry, Stock Ledger, Stock Balance, Stock Reservation, reserve/unreserve, and stock movement blocked.

### W16F - Activate Cycle Count / Inventory Variance Workflow UI

Goal: replace `Cycle counts` and `Inventory variance` planned Action Center cards plus Overview planned shell with active custom count and variance review queues.

Scope:
- Add custom cycle count task entry and manager variance decision UI.
- Add Inventory/Admin handoff request UI.
- Keep Stock Reconciliation and Stock Entry blocked.

### W16G - Overview Planned-State Burn-Down

Goal: remove or rename all remaining planned/shell-only owner-facing states.

Scope:
- Replace `Planned workflow shells` section with an active `Controlled workflow lanes` or `Workflow workbench` section.
- Convert active lanes to route/action cards backed by custom workflow state.
- Retain blocked ERP document guardrails as policy badges, not as fake buttons.
- Run owner manual UI review.

### W16H - Real Warehouse Workspace Closure Audit

Goal: verify the workspace is actually closable.

Closure bar:
- No business-critical Overview card remains as `Planned` without an owner-approved reason.
- No shell-only controls remain on receiving/picking/returns/transfer/cycle-count pages unless explicitly documented as intentionally blocked ERP document policy.
- Every active custom workflow has tests, smoke coverage, role gates, idempotency, and no-effect flags.
- No ERPNext stock/accounting document behavior is activated accidentally.
- Owner manually accepts the full Warehouse Overview and major workflow pages.

## 6. Priority Decision

Recommended immediate next phase: W16B Inbound Receiving Custom Workflow UI Activation.

Reason:
- It is the safest first runtime activation because receiving already has a live review route and backend custom task methods.
- It removes an obvious shell-only section from an existing operational page.
- It builds the UI activation pattern that W16C-W16F can reuse.

## 7. Review Policy For W16 Runtime Phases

Use Hybrid Review Ladder:
- Internal subagents may preflight bounded UI/runtime patches in the main thread.
- Separate Hardening, Security/Stability, and Operations agents must review major runtime activations before commit.

For every W16 runtime phase, require:
- Simple plan before implementation.
- Source validation before review.
- Manual owner UI check when visible behavior changes.
- No commit until owner approval.
- Push only after separate owner approval.

## 8. Boundary Confirmation

W16A is docs-only. It does not implement, enable, commit, push, live-align, restart, or approve any planned workflow activation. It defines the path to real Warehouse Workspace Closure and keeps ERPNext stock/accounting/native-route/notification behavior blocked until separate owner/security-approved phases.
