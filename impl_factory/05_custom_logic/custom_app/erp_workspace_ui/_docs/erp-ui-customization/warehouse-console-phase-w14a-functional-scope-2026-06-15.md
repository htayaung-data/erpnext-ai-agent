# Warehouse Console Phase W14A Functional Scope

Date: 2026-06-15

Status: `superseded_by_w15a_operations_blueprint`

Superseded by:

- `warehouse-console-phase-w15a-operations-blueprint-2026-06-16.md`

Use this W14A document as historical planning input only. The active Warehouse operations roadmap after Phase 0 is W15A-W15J. Future agents should not continue W14 phase naming unless Main Control explicitly reopens it.

Decision: `scope_rebased_after_phase0_ready_for_w14d_inbound_arrival_design`

Scope: docs-only functional planning and governance boundary. This phase does not implement runtime features, backend methods, routes, smokes, live alignment, or stock actions.

Phase 0 live rebaseline, 2026-06-16:

- Warehouse Quick Find is no longer a cockpit content block. It is now the shared sidebar Search helper, following the Sales/Procurement utility pattern and routing only to custom Warehouse routes.
- The duplicated Overview Manager Readiness component has been removed. Manager work must return later as workflow-specific action readiness, not as another overview KPI section.
- The next functional design step is inbound arrival/readiness workflow design, still without Purchase Receipt creation, stock posting, supplier messaging, or native ERP escape.

## Purpose

Warehouse Console now has a confirmed premium UI direction for the read-only workspace. The next work must not jump directly into execution buttons or broad WMS behavior. W14A defines the functional scope, role boundaries, and implementation sequence for moving from read-only review to a governed warehouse operations workspace.

The immediate goal is to decide what Warehouse should include, what it should borrow from Sales and Procurement console patterns, and what must remain blocked until owner, Security/Stability, Operation Review, and Main Control approve a specific implementation phase.

## Current Warehouse Baseline

The current Warehouse Console surfaces are protected custom routes:

- `/desk/warehouse-console`
- `/desk/warehouse-console-worklist/inbound-receiving`
- `/desk/warehouse-console-receiving/<purchase-order>`
- `/desk/warehouse-console-worklist/outbound-picking`
- `/desk/warehouse-console-picking/<sales-order>`
- `/desk/warehouse-console-worklist/stock-exceptions`
- `/desk/warehouse-console-stock-exception/<encoded-context>`
- `/desk/warehouse-console-stock-posture/<encoded-context>`
- `/desk/warehouse-console-worklist/movement-visibility`
- `/desk/warehouse-console-movement/<encoded-context>`
- `/desk/warehouse-console-worklist/transfer-visibility`

Accepted baseline behavior:

- Review-only Warehouse workspace.
- Custom Warehouse routes only.
- No native ERPNext Form/List/Report escape.
- Warehouse Quick Find exists only as the shared sidebar Search helper; no cockpit Quick Find block remains.
- No duplicated Manager Readiness Center on the Overview page.
- No Stock Entry, Purchase Receipt, Delivery Note, Pick List, Stock Reservation, or Stock Reconciliation creation.
- No submit, cancel, amend, post, reserve, unreserve, reconcile, transfer, receive, pick, pack, ship, deliver, or adjust action.
- No valuation, accounting, price, margin, billing, payment, or commercial exposure.
- No Sales runtime change and no Procurement runtime change.

## Inputs From Sales And Procurement Console

Warehouse should reuse proven console patterns instead of inventing a separate product model.

Patterns to reuse:

- Premium overview as a role-aware work entry point.
- Quick Find with preview-first behavior and explicit open actions.
- Work queues grouped by operational posture.
- Detail pages that explain context before action.
- Manager readiness and exception review before any lifecycle action.
- Custom managed routes instead of raw ERPNext native route escape.
- Stable smoke selectors and protected workspace gates.
- Copy that separates review, recommendation, request, approval, and execution.

Patterns not to copy blindly:

- Sales owns customer communication, quotations, orders, and commercial follow-up.
- Procurement owns supplier communication, RFQ, supplier quotation, purchase order, item buying readiness, and commercial buying context.
- Warehouse must not become a backdoor to Sales, Procurement, Finance, or stock ledger mutation.

## Inputs From Common ERP/WMS Scope

Common warehouse operations usually include:

- Inbound receiving.
- Arrival discrepancy capture.
- Quality check or inspection signal.
- Putaway guidance.
- Outbound picking and packing readiness.
- Shipment or dispatch readiness.
- Internal transfer review.
- Cycle count and adjustment request.
- Stock exception and replenishment signal.
- Barcode or mobile scan capture.
- Warehouse task assignment and manager oversight.

W14 should not implement all of these at once. The safe path is to add read-only discovery first, then readiness/request workflows, then separately govern any write-capable actions.

## Role Model

### Warehouse User

Primary responsibility:

- Review assigned inbound, outbound, exception, movement, and transfer work.
- Inspect line-level warehouse facts.
- Identify readiness, shortage, overage, damage, missing warehouse, and timing issues.
- Prepare evidence for manager review when a future request workflow exists.

Allowed in near-term W14:

- Use Warehouse Quick Find when implemented.
- Open custom Warehouse routes.
- Review line detail and related context.
- View role-visible readiness and exception state.
- Prepare non-mutating review input only when a later phase explicitly adds it.

Forbidden until separately approved:

- Submit or create stock documents.
- Approve adjustments or transfers.
- Reserve or unreserve stock.
- Send customer or supplier messages.
- Access valuation, accounting, price, margin, or billing content.
- Open native ERPNext Form/List/Report pages from Warehouse.

### Warehouse Manager

Primary responsibility:

- Triage warehouse exceptions and readiness blockers.
- Review arrival, picking, transfer, and inventory-control evidence.
- Decide whether a case is ready for a later governed action workflow.
- Coordinate with Procurement for supplier/PO issues and Sales for customer/order issues.

Allowed in near-term W14:

- Use Warehouse Quick Find when implemented.
- Review manager readiness and exception queues.
- Approve or reject readiness only if a future phase explicitly implements a non-stock-mutating readiness workflow.
- Route cases to the correct custom Warehouse detail page.

Forbidden until W14H or later:

- Directly submit Purchase Receipts, Delivery Notes, Pick Lists, Stock Entries, Stock Reconciliations, or Stock Reservations.
- Trigger stock posting, ledger changes, valuation changes, or accounting impact.
- Override Procurement-owned supplier/PO commercial decisions.
- Override Sales-owned customer communication or delivery promise decisions.

### Procurement Team

Procurement owns:

- Supplier communication.
- Purchase Requests, RFQs, Supplier Quotations, Purchase Orders.
- Buying readiness, supplier commercial context, pricing, supplier disputes, and PO policy.

Warehouse may provide:

- Arrival facts.
- Received/open quantity posture.
- Discrepancy signals.
- QC or damage notes after a future approved request workflow.

Warehouse must not own:

- Supplier negotiation.
- Purchase price or commercial terms.
- PO approval, amendment, cancellation, or supplier messaging.

### Sales Team

Sales owns:

- Customer communication.
- Sales Orders, quotations, delivery promise, commercial follow-up.
- Customer-facing exception messaging.

Warehouse may provide:

- Pick/pack readiness.
- Availability posture.
- Movement/dispatch evidence.
- Shipment readiness signal after a future approved request workflow.

Warehouse must not own:

- Customer email/send actions.
- Sales order amendment, cancellation, pricing, discounts, or delivery promise change.

### System/Admin

System/Admin owns:

- Permission configuration.
- Governance manifests.
- Protected gates.
- Workspace routing policy.
- Audit posture and deployment control.

## Functional Ownership Matrix

| Functional area | Warehouse role | Cross-console owner | Initial W14 mode | Later write candidate | W14 forbidden boundary |
| --- | --- | --- | --- | --- | --- |
| Quick Find | Find warehouse work and records | None, but route policy is shared | Read-only custom-route search | No write candidate | No native ERP search escape |
| Inbound arrival review | Inspect arrival readiness and discrepancies | Procurement owns PO/supplier | Review and readiness planning | Purchase Receipt draft only after separate approval | No Purchase Receipt creation/submission in W14D |
| Quality/damage signal | Flag receiving concern | Procurement/Quality policy | Review signal only | Quality Inspection or hold workflow after separate approval | No stock hold/release mutation |
| Putaway readiness | Identify where stock should go | Warehouse | Review guidance only | Putaway task workflow after separate approval | No Bin or stock mutation |
| Outbound pick/pack readiness | Inspect pickability and open demand | Sales owns customer/order | Review and readiness planning | Pick List/Delivery Note draft only after separate approval | No reserve, pick, pack, ship, deliver |
| Transfer request review | Inspect warehouse-to-warehouse movement needs | Warehouse | Review and readiness planning | Stock Entry draft only after separate approval | No transfer posting |
| Cycle count/adjustment request | Identify variance and request review | Warehouse/Finance control | Request planning only | Stock Reconciliation request after separate approval | No valuation or stock adjustment |
| Replenishment signal | Surface shortage/inbound cover | Procurement owns buying action | Read-only signal | Material Request/Purchase Request candidate after separate approval | No automatic PR/MR/PO |
| Customer shipment communication | Provide readiness evidence | Sales owns customer contact | Warehouse-readiness only | Sales-owned send action, not Warehouse-owned | No customer send/email from Warehouse |
| Barcode/mobile scan | Improve evidence capture | Warehouse/Admin | Deferred design | Capture workflow after separate approval | No ungoverned scan-to-post behavior |

## W14 Phase Sequence

W14 must proceed in small, reviewable phases.

### W14B - Warehouse Quick Find

Status after Phase 0:

- Implemented as shared sidebar Search helper.
- Cockpit Quick Find block removed.
- Custom Warehouse route targets only.
- No native ERPNext global search behavior.
- No stock mutation or valuation exposure.

Goal:

- Add a Warehouse-owned Quick Find pattern consistent with Sales/Procurement, but scoped to custom Warehouse routes only.

Initial result types:

- Purchase Order receiving review.
- Sales Order picking review.
- Stock exception review.
- Item/warehouse stock posture.
- Movement review.
- Transfer visibility or movement context.

Rules:

- Preview before open.
- Role-scoped results.
- No native ERPNext result targets.
- No write actions.
- No valuation, price, margin, billing, or accounting snippets.
- No Sales or Procurement runtime changes.

### W14C - Workflow-Specific Manager Readiness

Status after Phase 0:

- Do not restore the removed Overview Manager Readiness component.
- Manager work should appear where the work happens: inbound arrival, outbound pick/pack, transfer review, inventory-control request, or exception review.
- Any manager action must be explicit about whether it is review-only, non-mutating state capture, or a later governed stock-document write.

Goal:

- Define Warehouse Manager readiness work without duplicating existing Overview sections or implying stock execution.

Candidate groups:

- Arrival needs manager review.
- Pick/pack blocked.
- Transfer needs review.
- Stock posture issue.
- Discrepancy or low-detail/unavailable data.

Rules:

- Review-only unless a later sub-phase explicitly adds non-mutating state capture.
- No lifecycle documents.
- No approval that implies stock posting.
- No standalone Overview readiness dashboard unless the owner asks for a true manager inbox after workflow pages prove the need.

### W14D - Inbound Arrival Review

Goal:

- Add a better operational review surface for supplier arrival and discrepancy readiness.

Candidate facts:

- Expected vs arrived quantity.
- Over/short/damaged/missing line signal.
- Warehouse target.
- QC required signal.
- Procurement follow-up required signal.

Rules:

- Do not create or submit Purchase Receipt.
- Do not update PO.
- Do not post stock.
- Do not expose valuation.
- Any future Purchase Receipt draft must be a separate, owner-approved, manager-only write phase.

### W14E - Outbound Pick/Pack Readiness

Goal:

- Add warehouse-owned pick/pack readiness review while preserving Sales ownership of customer/order communication.

Candidate facts:

- Pickable lines.
- Short lines.
- Warehouse readiness.
- Pack readiness.
- Sales follow-up required signal.

Rules:

- Do not create Pick List or Delivery Note.
- Do not reserve or unreserve stock.
- Do not ship or deliver.
- Do not send customer communication from Warehouse.

### W14F - Inventory Control Requests

Goal:

- Add review/request planning for stock variance, cycle count, adjustment, and reconciliation candidates.

Candidate facts:

- Item and warehouse.
- Expected posture.
- Count variance signal.
- Evidence captured.
- Manager review state.

Rules:

- Do not create or submit Stock Reconciliation.
- Do not expose valuation/accounting.
- Do not adjust stock.

### W14G - Transfer Request Review

Goal:

- Add request/readiness workflow for warehouse-to-warehouse movement needs.

Candidate facts:

- Source warehouse.
- Target warehouse.
- Quantity.
- Availability.
- Reason.
- Manager readiness.

Rules:

- Do not create or submit Stock Entry.
- Do not execute transfer.
- Do not expose Stock Ledger/Stock Balance native reports.

### W14H - Write Governance Decision

Goal:

- Decide whether any Warehouse writes are allowed, and if so, which exact document, role, route, payload, validation, audit, smoke, and protected gate are required.

No write implementation should start before W14H.

Required before any write:

- Owner approval of the exact action.
- Security/Stability acceptance.
- Operation Reviewer acceptance.
- Protected source gate.
- Credentialed source smoke.
- Live alignment plan.
- Live protected gate.
- Clear rollback plan.

## Quick Find Scope For W14B

Phase 0 outcome:

- This is now implemented as a sidebar utility and should stay there.
- Future work should harden result quality and role scope, not move it back into the Overview content.

Warehouse Quick Find should be the first implemented feature because it improves usability without changing data.

Allowed behavior:

- Search custom Warehouse-visible records.
- Show grouped suggestions with compact preview facts.
- Open only custom Warehouse routes.
- Use explicit open buttons rather than automatic navigation.
- Keep user and manager result scopes role-aware.
- Keep no-result and restricted-result states controlled.

Initial queryable keys:

- Purchase Order number and supplier for receiving.
- Sales Order number and customer for picking.
- Item code/item name.
- Warehouse name.
- Movement reference.
- Transfer source/target warehouse.

Forbidden behavior:

- Global ERPNext Quick Find.
- Native `/desk/Form`, `/desk/List`, `/desk/Report`, `/app`, or query-report targets.
- Stock Ledger, Stock Balance, Stock Reconciliation, Stock Entry, Purchase Receipt, Delivery Note, Pick List, or Stock Reservation native targets.
- Any mutation, reservation, submission, posting, or cancellation.
- Valuation/accounting/commercial snippets.

## Manager Action Taxonomy

Use precise language in future implementation.

### Safe language

- Review
- Inspect
- Open
- Preview
- Readiness
- Needs review
- Request review
- Prepare evidence
- Manager review required

### Conditional language

These terms require a specific future phase:

- Approve readiness
- Reject readiness
- Assign
- Request correction
- Mark reviewed
- Hold for review

### Forbidden language until W14H or later

- Receive now
- Pick now
- Pack now
- Ship
- Deliver
- Post
- Submit
- Cancel
- Amend
- Reserve
- Unreserve
- Reconcile
- Adjust stock
- Create Purchase Receipt
- Create Delivery Note
- Create Pick List
- Create Stock Entry
- Create Stock Reconciliation
- Send to customer
- Send to supplier

## Data And Security Requirements

All future W14 implementation phases must preserve these requirements:

- Role-scoped service responses.
- No parent document fallback that broadens visibility.
- Escaped dynamic text in runtime renderers.
- Stable selectors for smoke and visual evidence.
- Duplicate-route and stale-response protection for new async routes.
- Explicit empty, low-detail, and restricted states.
- Source smokes before review acceptance.
- Protected workspace gate before commit or live alignment.
- No Sales/Procurement runtime changes unless a separate approved cross-console phase explicitly requires them.

## Acceptance Checklist For W14A

W14A is complete when:

- This docs-only scope exists.
- README records W14A as the next governance step after W13.
- No runtime, backend, smoke, package, live, Sales, or Procurement file is changed.
- W14B is limited to Warehouse Quick Find unless owner/Main Control changes the sequence.
- Future manager actions remain blocked until W14H write governance or a separately approved non-mutating readiness phase.

## Recommendation

Proceed next to W14D Inbound Arrival Readiness Design as the first post-Phase-0 functional design package.

Do not start receiving, picking, transfer, reconciliation, barcode, mobile, customer-send, supplier-send, or stock-posting implementation until the relevant W14 scope phase is accepted.
