# Warehouse Console Phase W15D5 Delivery Note Dispatch Policy

Date: 2026-06-21

Status: docs-only Warehouse policy and design gate. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W15D outbound picking and dispatch workflow design.
- W15D2 Picking Review workflow UI shell.
- W15D3 custom Warehouse Picking Task draft backend.
- W15D4 custom Warehouse Picking Task manager decisions.
- Current protected outbound routes:
  - `/desk/warehouse-console-worklist/outbound-picking`.
  - `/desk/warehouse-console-picking/<sales-order>`.

## 1. Title And Scope

W15D5 defines the policy boundary for outbound dispatch handoff and any future Delivery Note draft request from Warehouse Console.

This is a design gate only. It does not approve runtime implementation. It does not approve Delivery Note draft creation. It does not approve Delivery Note submission. It does not approve Pick List creation, stock reservation, Stock Entry, Stock Ledger mutation, customer notification, Sales Order update, or stock posting.

The purpose is to separate the internal Warehouse readiness state from ERPNext delivery and stock movement documents before any future implementation phase is considered.

W15D5 must not:

- Create Delivery Note.
- Prepare Delivery Note draft.
- Submit Delivery Note.
- Create Pick List.
- Create Stock Reservation.
- Reserve or unreserve stock.
- Create Stock Entry.
- Mutate Stock Ledger.
- Post stock.
- Expose native ERPNext routes.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.
- Expose valuation, accounting, billing, payment, tax, margin, profit, rate, amount, price, cost, or commercial fields.

## 2. Current W15D State

The current outbound execution-readiness track is intentionally limited to custom Warehouse records and custom Warehouse routes.

Current state:

- W15D2 adds a Picking Review workflow shell on the custom Warehouse Picking Review page.
- W15D3 adds custom internal `Warehouse Picking Task` draft evidence saving.
- W15D4 adds custom internal `Warehouse Picking Task` manager decisions.
- Current allowed state ends at internal custom task decisions such as `Pack Ready` and `Dispatch Handoff Ready`.
- The custom task records are not ERPNext stock documents.
- The custom task records do not create Delivery Note, Pick List, Stock Reservation, Stock Entry, or Stock Ledger entries.
- No Delivery Note draft exists from Warehouse Console.
- No Delivery Note submission exists from Warehouse Console.
- No stock posting exists from Warehouse Console.

`Dispatch Handoff Ready` is therefore only a Warehouse-side readiness signal. It is not shipping, delivery, or stock posting.

## 3. Business Flow In Plain English

Outbound demand starts from a Sales Order. Sales owns the customer promise and the commercial/customer-facing side of the order.

Warehouse sees the outbound picking work in Warehouse Console. Warehouse users physically pick and pack goods, then record evidence in the custom Warehouse picking task. If goods are short, damaged, not found, substituted, or otherwise questionable, Warehouse records that evidence instead of hiding it.

Warehouse Manager reviews the custom picking task. The manager may approve a clean pick, approve a partial pick, mark shortage review, request repick, escalate to Sales, mark pack ready, or mark dispatch handoff ready.

Sales owns customer-facing changes and partial shipment confirmation. Sales or Admin owns Delivery Note governance unless a later owner-approved policy explicitly permits a controlled Warehouse request service.

ERPNext remains the system of record for actual Delivery Notes and stock movement. Stock changes happen only when ERPNext stock documents are submitted through an approved process outside this W15D5 policy document.

## 4. Dispatch Handoff Policy

`Dispatch Handoff Ready` means:

- Warehouse has completed its internal readiness review.
- Goods are physically picked, packed, and checked according to the available task evidence.
- Required exception evidence is present.
- Manager has approved the readiness state.
- The task is ready for a downstream document or Sales/Admin decision process.

`Dispatch Handoff Ready` does not mean:

- Goods have shipped.
- Goods have been delivered.
- Stock has been posted.
- Sales Order has been updated.
- Customer has been notified.
- Delivery Note has been created.
- Delivery Note draft has been prepared.
- Delivery Note has been submitted.
- Pick List has been created.
- Stock has been reserved.

Visible Warehouse copy should use careful language such as `Dispatch handoff ready` or `Ready for dispatch handoff`. It must not use `Shipped`, `Delivered`, `Posted`, or `Delivery Note created` unless a future approved ERPNext document state actually supports that claim.

## 5. Delivery Note Draft Policy Options

### Option A: Warehouse Requests Delivery Note Draft; Sales/Admin Owns Draft

Warehouse records the handoff state and requests that Sales/Admin prepare or review the Delivery Note draft. Warehouse does not create the ERPNext Delivery Note document.

This is the recommended default.

Why this is safest:

- Sales keeps ownership of customer-facing partial shipment decisions.
- Admin/Sales keeps ownership of Delivery Note governance.
- Warehouse remains focused on physical evidence and readiness.
- Native ERPNext submit bypass risk is lower because Warehouse does not hold a Delivery Note draft route or draft document handle.
- No Warehouse stock posting is introduced.

### Option B: Controlled Warehouse Service Prepares Unsubmitted Draft After Sales/Admin Approval

A future service could prepare an unsubmitted Delivery Note draft only after Sales/Admin approval and strict policy checks. This would still be a mutation and requires separate Security/Stability and owner approval.

Required limits if ever approved:

- Manager-level Warehouse role plus Sales/Admin approval reference.
- Server-side Sales Order and line validation.
- Explicit accepted dispatch quantity.
- Strict idempotency.
- No submit call.
- No native route exposure.
- Plain text draft reference only unless native-submit bypass containment is solved.

This is a future option only. It is not approved by W15D5.

### Option C: Direct Warehouse Delivery Note Creation Or Submission

Reject and block.

Direct Warehouse Delivery Note creation/submission would blur Warehouse readiness with ERPNext stock posting and customer-facing delivery governance. It also increases native-submit bypass, stock ledger, and Sales Order side-effect risk.

W15D5 rejects this option.

## 6. Eligibility Rules For Any Future Delivery Note Draft Or Request

Any future request or draft preparation must require all of these conditions:

- A custom `Warehouse Picking Task` exists.
- The task belongs to a Warehouse-visible Sales Order.
- The task has a manager-approved state.
- The task is `Dispatch Handoff Ready`, `Clean Pick Approved`, or `Partial Pick Approved` under approved policy.
- Accepted dispatch quantity is explicit and server-computed or server-validated.
- Packed quantity supports the dispatch quantity.
- No unresolved damaged lines exist.
- No unresolved not-found lines exist.
- Shortage or partial dispatch has Sales approval.
- Customer-facing issue is resolved or acknowledged by Sales.
- Sales Order line mapping is valid.
- Source warehouse validation passes.
- Every line belongs to the visible task and visible Sales Order context.
- Request idempotency is enforced.
- Audit event is appended.
- Returned payload has all stock-effect flags false during request-only phases.

The future method must reject client-supplied trusted ERPNext document fields. Sales Order, line, warehouse, item, and quantity eligibility must be derived or validated server-side.

## 7. Exclusion Rules

Block Delivery Note draft/request by default when any of these are true:

- Damaged goods are unresolved.
- Not-found goods are unresolved.
- Shortage is unresolved.
- Substitution lacks Sales/customer approval.
- Partial dispatch lacks Sales approval.
- Wrong warehouse is present.
- A line is not visible through Warehouse Console.
- A line does not belong to the task's Sales Order.
- Packed quantity is lower than accepted dispatch quantity.
- Dispatch quantity is zero or negative.
- Customer-facing issue is not acknowledged.
- Idempotency key is missing or reused across another task.
- Native route exposure is needed.
- Valuation, rate, amount, account, tax, margin, profit, cost, billing, payment, or customer commercial terms are needed.

A blocked state should return a business-safe reason and append an audit event only if the attempt represents an operational decision. It must not expose stack traces or internal ERPNext errors.

## 8. Role Ownership

### Warehouse User

Warehouse User owns physical pick and pack evidence only.

Allowed future responsibilities:

- Record picked quantity.
- Record packed quantity.
- Record shortage, damage, not-found, substitution, wrong-bin, and paperwork mismatch evidence.
- Add notes and evidence reference.
- Submit the custom task for manager review.

Forbidden:

- Create Delivery Note.
- Prepare Delivery Note draft.
- Submit Delivery Note.
- Create Pick List.
- Reserve stock.
- Post stock.
- Update Sales Order.
- Notify customer.

### Warehouse Manager / Stock Manager

Warehouse Manager and Stock Manager own internal readiness and dispatch handoff approval.

Allowed future responsibilities:

- Approve clean pick.
- Approve partial pick when policy allows.
- Mark shortage review.
- Request repick.
- Mark pack ready.
- Mark dispatch handoff ready.
- Request Delivery Note draft preparation only if a later policy explicitly approves request-only behavior.

Forbidden by W15D5:

- Submit Delivery Note.
- Post stock.
- Override Sales-owned customer-facing decisions.
- Create native Delivery Note links in Warehouse UI.

### Sales User / Sales Manager

Sales owns customer-facing outbound governance.

Responsibilities:

- Approve customer-facing partial shipment.
- Approve customer promise changes.
- Own customer notification.
- Own Sales Order governance.
- Resolve customer-facing shortage or substitution decisions.

### System/Admin

System/Admin owns policy configuration and document governance.

Responsibilities:

- Configure roles and warehouse scope.
- Configure dispatch evidence requirements.
- Configure partial dispatch approval rules.
- Configure document owner policy.
- Review native-submit bypass containment before any draft runtime.

### Procurement

Procurement is not normally involved in outbound dispatch handoff. Procurement may become involved only if a supplier-side issue impacts outbound stock posture and requires supplier correction or sourcing follow-up.

### ERPNext

ERPNext remains the system of record for Delivery Note and Stock Ledger. Warehouse Console may only display bounded custom status or request posture until a later approved ERPNext document policy exists.

## 9. Required Evidence

Any future dispatch handoff or Delivery Note request must preserve this evidence:

- Pick task id.
- Sales Order id.
- Sales Order line mapping.
- Item code and warehouse.
- Pick task line quantities.
- Picked quantity.
- Packed quantity.
- Accepted dispatch quantity.
- Short quantity, damaged quantity, and not-found quantity where present.
- Exception notes.
- Evidence reference for exception lines.
- Pack reference.
- Package count.
- Dispatch handoff note.
- Manager event.
- Manager actor and timestamp.
- Sales approval reference for partial or customer-facing dispatch.
- Idempotency request id.

Evidence must be stored in custom Warehouse task records or approved event records. Do not store valuation, rate, amount, tax, margin, profit, cost, account, billing, payment, or customer commercial terms in Warehouse task evidence.

## 10. Future Data Model Additions

Design only. Do not implement in W15D5.

Potential future fields on `Warehouse Picking Task Line`:

- `accepted_for_dispatch_qty`.
- `dispatch_handoff_reference`.
- `pack_reference`.
- `package_count`.
- `sales_approval_reference`.

Potential future fields on `Warehouse Picking Task`:

- `delivery_note_request_status`.
- `delivery_note_reference_text`.
- `dispatch_handoff_at`.
- `dispatch_handoff_by`.
- `dispatch_handoff_note`.
- `dispatch_policy_version`.

Potential future event types:

- `dispatch_handoff_requested`.
- `dispatch_handoff_marked`.
- `delivery_note_request_created`.
- `delivery_note_request_blocked`.
- `delivery_note_request_idempotent_replay`.

These fields and events require a separate implementation phase, tests, and owner approval.

## 11. Native Route And Submit Bypass Containment

Before any runtime implementation, Security/Stability must review native-submit bypass risk.

Required containment rules:

- No native Delivery Note links in Warehouse UI.
- No `/app` route targets.
- No `/desk/Form` route targets.
- No `/desk/List` route targets.
- No `/desk/Report` route targets.
- No `/desk/query-report` route targets.
- No workspace route escape to native Stock, Selling, or Delivery Note pages.
- No submit button.
- No disabled submit button.
- No print button.
- No email button.
- No draft open button that lands on a native ERPNext form.

If a future draft reference is shown, it should be plain text/status only until native-submit bypass containment is approved. Warehouse users should not be able to click into a native Delivery Note form from Warehouse Console.

## 12. Test Plan For Future Implementation

Future implementation tests must include:

- Clean dispatch handoff allowed only from a manager-approved clean or pack-ready task.
- Partial handoff requires Sales approval reference.
- Damaged lines block request or draft preparation.
- Not-found lines block request or draft preparation.
- Unresolved shortage blocks request or draft preparation.
- Substitution without Sales/customer approval blocks request or draft preparation.
- Wrong warehouse blocks request or draft preparation.
- Invisible lines block request or draft preparation.
- Idempotency returns the same safe result for the same request id.
- Request id reuse across another task is rejected.
- Request-only phase creates no Delivery Note.
- Request-only phase creates no Pick List.
- Request-only phase creates no Stock Reservation.
- Request-only phase posts no stock.
- No native route is returned.
- No valuation, rate, amount, account, tax, margin, profit, cost, billing, payment, or customer commercial field is returned.
- No Sales Order update occurs unless a later owner-approved phase explicitly allows it.
- No customer notification occurs unless a later owner-approved phase explicitly allows it.
- Audit event is appended for manager decisions and request attempts.
- Warehouse User is denied manager and request actions.
- Sales/User roles do not receive Warehouse execution rights unless explicitly approved later.

Smoke coverage for a future UI phase should also verify that any dispatch or request panel remains custom Warehouse UI only and has no native ERPNext route leakage.

## 13. Open Owner Decisions

Owner decisions needed before any runtime implementation:

- Can Warehouse Manager request Delivery Note draft preparation, or only Sales/Admin?
- Is Sales Manager approval mandatory for every partial dispatch?
- Who owns customer notification?
- Is Pick List integration ever allowed?
- Is Stock Reservation ever allowed?
- Can Warehouse see Delivery Note reference text?
- What is required as pack/handoff evidence?
- Is package count mandatory?
- Who closes dispatch-ready tasks?
- Who cancels dispatch-ready tasks?
- How should repick requests reopen or supersede pack-ready tasks?
- How should native submit bypass be prevented for draft Delivery Notes?
- Should request-only dispatch handoff create a custom request record or only append task events?
- Which roles can see Sales approval references in Warehouse Console?

## 14. Recommended Next Phase

W15D6 should not create Delivery Notes unless owner, Security/Stability, and operational decisions are resolved.

Preferred next runtime phase:

- Add request-only dispatch handoff state or a custom Delivery Note request record.
- Keep it inside custom Warehouse routes.
- Keep all stock-effect flags false.
- Create no Delivery Note draft.
- Create no Pick List.
- Create no Stock Reservation.
- Post no stock.
- Return no native routes.

Delivery Note draft preparation should remain a later phase after native-submit bypass containment, Sales approval policy, document ownership, idempotency, and audit behavior are explicitly accepted.
