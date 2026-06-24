# Warehouse Console Phase W15H Operations Closure And Next Scope Decision

Date: 2026-06-24

Status: docs-only Warehouse roadmap decision package. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, pushes, stock document behavior, or native ERPNext route exposure.

Related baseline:

- W15A Warehouse operations blueprint.
- W15C inbound receiving custom evidence and manager posture track.
- W15D outbound picking and dispatch handoff track.
- W15E customer return intake and Sales/Admin handoff track.
- W15F supplier return candidate and Procurement/Admin handoff track.
- W15G internal transfer candidate and Inventory/Admin handoff track.
- W15G10 internal transfer closure accepted on 2026-06-24.

## 1. Title And Scope

W15H records the next-scope decision after the W15C through W15G Warehouse workflow tracks.

This is a decision package only. It does not approve implementation. It does not add UI, services, DocTypes, tests, smokes, or live changes.

The purpose is to prevent scope drift after completing receiving, outbound picking, returns, supplier returns, and internal transfer foundations. W15H chooses the next safe direction before more runtime work starts.

W15H must not:

- Create Stock Entry.
- Save Stock Entry.
- Submit Stock Entry.
- Cancel Stock Entry.
- Amend Stock Entry.
- Create Stock Reconciliation.
- Save Stock Reconciliation.
- Submit Stock Reconciliation.
- Create Stock Reservation.
- Reserve stock.
- Unreserve stock.
- Mutate Stock Ledger.
- Mutate Stock Balance.
- Move stock.
- Post stock.
- Create Purchase Receipt, Delivery Note, Sales Return, Credit Note, return Purchase Receipt, Purchase Invoice return, or debit note.
- Trigger customer notification.
- Trigger supplier notification.
- Send email.
- Open portal access.
- Expose native ERPNext routes.
- Expose `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report` native route patterns.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.
- Expose valuation, accounting, billing, payment, tax, landed cost, margin, profit, rate, amount, price, cost, debit, credit, payable, GL, or commercial fields.

## 2. Current Warehouse Coverage

The Warehouse Console now has controlled foundations for:

- Inbound receiving evidence and manager decisions.
- Purchase Receipt draft policy documentation.
- Outbound picking evidence, manager decisions, and dispatch handoff request.
- Delivery Note dispatch policy documentation.
- Customer return intake, manager decisions, and Sales/Admin handoff request.
- Customer return Sales/Admin handoff policy documentation.
- Supplier return candidate, manager decisions, and Procurement/Admin handoff request.
- Supplier return Procurement/Admin handoff policy documentation.
- Internal transfer candidate, manager decisions, Inventory/Admin handoff request, and Stock Entry draft policy documentation.

These foundations are deliberately request-only/custom-record-first. They do not post stock, mutate ERPNext stock documents, expose native ERPNext routes, or expose valuation/accounting/commercial fields.

## 3. Remaining Major Warehouse Gap

The major remaining Warehouse operations gap is inventory control:

- Cycle count planning.
- Physical inventory count evidence.
- Recount workflow.
- Variance classification.
- Manager variance review.
- Inventory/Admin adjustment review.
- Future Stock Reconciliation policy.

This gap appears in the current Warehouse Overview as planned `Cycle counts` and `Inventory variance` lanes. It should not be filled by jumping directly to Stock Reconciliation or Stock Entry behavior.

The safe sequence is:

1. Docs-only cycle count / inventory variance design.
2. UI-only shell or compact overview lane if needed.
3. Custom metadata for count tasks.
4. Custom draft evidence save.
5. Manager variance decision.
6. Request-only Inventory/Admin variance handoff.
7. Stock Reconciliation policy documentation.
8. Only later, owner-approved ERPNext document runtime if needed.

## 4. Decision Options

### Option A: Proceed To W15H1 Cycle Count / Inventory Variance Design

Recommended.

This option creates a docs-only policy and workflow design for cycle counts and inventory variance. It defines roles, statuses, evidence, count-line rules, recount decisions, variance posture, Inventory/Admin handoff, and blocked ERPNext mutation boundaries.

Why this is best:

- It fills the largest remaining Warehouse operations gap.
- It keeps the same safe pattern used in W15C through W15G.
- It avoids premature Stock Reconciliation or Stock Entry implementation.
- It gives owner/security a chance to decide variance tolerance and stock adjustment ownership before runtime exists.

### Option B: Pause Runtime Work And Polish Overview Density

Acceptable if owner review finds the Warehouse Overview too dense.

This would keep runtime behavior unchanged and only refine the page organization, such as compact planned workflow shells, section spacing, and manual-review clarity.

This is not urgent because W15G10 manual review accepted the current Overview shell.

### Option C: Run A Warehouse Freeze / Protected Closure Package

Acceptable if the owner wants to freeze the current Warehouse scope before adding more workflows.

This would be a broader protected gate and documentation closure across W15C through W15G. It would not add features.

### Option D: Start Stock Entry Or Stock Reconciliation Runtime

Not recommended.

Stock document runtime is too high-risk without cycle count/variance policy and explicit owner/security decisions. Stock Entry and Stock Reconciliation should remain blocked until the custom evidence, manager review, request-only handoff, and policy gates are complete.

## 5. Recommended Decision

Recommended next phase: `proceed_to_w15h1_cycle_count_inventory_variance_design`.

W15H1 should be docs-only.

W15H1 should define:

- Cycle count task purpose.
- Count source types.
- Count scope.
- Warehouse/location scope.
- Item scope.
- Scheduled versus ad hoc count rules.
- Count evidence requirements.
- Blind count versus visible expected quantity policy.
- Recount policy.
- Variance classification.
- Variance tolerance policy.
- Manager review decisions.
- Inventory/Admin variance handoff.
- Future Stock Reconciliation policy boundary.
- Native route boundary.
- Valuation/accounting/commercial boundary.
- Test requirements before runtime.

W15H1 should not implement:

- UI runtime.
- Backend methods.
- DocTypes.
- Smokes.
- Stock Reconciliation.
- Stock Entry.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Reservation.
- Stock movement.
- Native ERPNext routes.

## 6. Proposed W15H Track

Proposed safe W15H track:

- W15H1: docs-only Cycle Count / Inventory Variance Workflow Design.
- W15H2: UI-only Overview shell or variance/cycle-count lane, if owner wants visual preview.
- W15H3: custom `Warehouse Cycle Count Task` metadata.
- W15H4: custom cycle count draft evidence backend.
- W15H5: manager recount / variance posture decisions.
- W15H6: docs-only Inventory/Admin variance handoff policy.
- W15H7: custom variance handoff request metadata.
- W15H8: request-only variance handoff backend.
- W15H9: docs-only Stock Reconciliation policy.
- W15H10: protected source gate and manual review closure.

Each runtime step must go through Hardening, Security/Stability, and Operations review before commit.

## 7. Role Ownership

Recommended ownership for W15H1:

- Warehouse User: physical count evidence only.
- Stock User: physical count evidence only where warehouse access allows.
- Warehouse Manager: recount decision and internal variance posture.
- Stock Manager: variance posture and Inventory/Admin handoff under policy.
- Inventory/Admin: stock adjustment policy and future Stock Reconciliation governance.
- System Manager: policy override and permission governance.
- Sales: not normally involved.
- Procurement: not normally involved unless variance relates to receiving dispute or supplier return.
- Finance/Admin: involved only if variance adjustment has accounting/write-off impact.

Warehouse should not own ERPNext Stock Reconciliation submission or accounting treatment.

## 8. Future Cycle Count Evidence Model

W15H1 should consider custom records only.

Possible future records:

- `Warehouse Cycle Count Task`.
- `Warehouse Cycle Count Task Line`.
- `Warehouse Cycle Count Task Event`.
- `Warehouse Inventory Variance Handoff Request`.
- `Warehouse Inventory Variance Handoff Request Line`.
- `Warehouse Inventory Variance Handoff Request Event`.

Possible evidence fields:

- Count task id.
- Count source.
- Warehouse.
- Location or bin reference as plain text only.
- Item code.
- Item name.
- UOM.
- Counted quantity.
- Expected quantity visibility policy.
- Variance quantity.
- Variance reason.
- Condition posture.
- Evidence reference as inert text.
- Recount status.
- Manager decision.
- Inventory/Admin handoff type.
- Request id.
- Source payload hash.
- Policy version.

Future records must not include native route, Link, Dynamic Link, Attach, Attach Image, HTML, Button, Currency, valuation, accounting, rate, amount, tax, cost, GL, Stock Ledger link, Stock Balance link, Stock Reconciliation link, Stock Entry link, email, portal, notification, or external-action fields unless later security review explicitly approves them.

## 9. Stock Reconciliation Boundary

Stock Reconciliation is blocked in W15H.

Any future Stock Reconciliation phase must be separate and owner/security approved.

Blocked until later approval:

- Stock Reconciliation draft creation.
- Stock Reconciliation save.
- Stock Reconciliation submit.
- Stock Reconciliation cancel.
- Stock Reconciliation amend.
- Stock Ledger mutation.
- Stock Balance mutation.
- Valuation rate exposure.
- Difference amount exposure.
- Accounting entry exposure.
- Native route exposure.

Default recommendation:

- Warehouse records physical count evidence.
- Warehouse Manager records internal variance posture.
- Inventory/Admin owns future reconciliation governance.
- Finance/Admin owns accounting impact if any.

## 10. Native Route Boundary

W15H does not approve native ERPNext route exposure.

Blocked route patterns:

- `/app`
- `/desk/Form`
- `/desk/List`
- `/desk/Report`
- `/desk/query-report`

Blocked native document/report examples:

- Stock Reconciliation form/list/report.
- Stock Entry form/list/report.
- Stock Ledger report.
- Stock Balance report.
- Stock Reservation form/list/report.
- Bin form/list/report.
- Item valuation reports.
- General Ledger report.

Future references, if shown, should remain plain text/status only until native-route containment is separately approved.

## 11. Valuation, Accounting, And Commercial Boundary

Warehouse count and variance UI/payload/custom records must not expose:

- Valuation rate.
- Stock value.
- Difference value.
- Rate.
- Amount.
- Base amount.
- Tax.
- Account.
- GL Entry.
- Payable.
- Payment.
- Billing.
- Landed cost.
- Margin.
- Profit.
- Cost.
- Debit.
- Credit.
- Price.
- Commercial terms.

Count variance should remain operational: item, warehouse, location/bin text, counted quantity, variance quantity, reason, evidence, recount posture, and review status.

## 12. Owner Decisions Before W15H Runtime

Before runtime implementation, owner/security should decide:

- Whether counts are scheduled, ad hoc, or both.
- Whether Warehouse users see expected quantity during count.
- Whether count is blind by default.
- Which warehouses are in scope.
- Whether bin/location text is enough or native Bin links are ever allowed.
- Whether serial/batch items are in scope.
- Whether count photos or attachments are allowed.
- Whether zero-count lines require manager note.
- Which variance tolerance requires manager review.
- Who can request recount.
- Who can close a count task.
- Whether Inventory/Admin approval is required for every variance.
- Whether Stock Reconciliation can ever be prepared from Warehouse Console.
- Whether Warehouse can see Stock Reconciliation reference text.
- Whether native Stock Reconciliation links are blocked permanently.
- Which protected gates are mandatory before live alignment.

## 13. W15H Acceptance Criteria

W15H is acceptable when:

- It remains docs-only.
- It records the completed W15C through W15G coverage.
- It identifies cycle count / inventory variance as the next major gap.
- It recommends W15H1 docs-only design as the next safe step.
- It blocks Stock Reconciliation and Stock Entry runtime.
- It blocks stock ledger/balance/reservation mutation.
- It blocks native ERPNext routes.
- It blocks valuation/accounting/commercial exposure.
- It blocks Sales/Procurement runtime changes.
- It blocks notification/email/portal/external actions.
- It records owner decisions before runtime.
- It updates README roadmap/status only.

## 14. Final Boundary Statement

W15H is a roadmap decision only.

The approved next recommendation is docs-only W15H1 Cycle Count / Inventory Variance Workflow Design. No Stock Reconciliation, Stock Entry, stock mutation, native route exposure, valuation/accounting/commercial exposure, Sales/Procurement runtime change, notification, email, portal, or external action is approved by W15H.
