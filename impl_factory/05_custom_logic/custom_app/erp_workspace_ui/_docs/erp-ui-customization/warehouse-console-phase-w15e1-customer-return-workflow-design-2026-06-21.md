# Warehouse Console Phase W15E1 Customer Return Workflow Design

Date: 2026-06-21

Status: docs-only Warehouse policy and design artifact. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W15C inbound receiving workflow and Purchase Receipt draft policy.
- W15D outbound picking, manager decision, dispatch handoff, and Delivery Note dispatch policy.
- Current protected Warehouse visibility routes remain custom Warehouse routes only.

## 1. Title And Scope

W15E1 defines a future Customer Return Workflow policy for Warehouse Console.

This is policy and design only. It does not approve runtime implementation. It does not approve ERPNext return document creation. It does not approve ERPNext return document submission. It does not approve stock mutation.

W15E1 must not:

- Create Sales Return.
- Create Credit Note.
- Create return Delivery Note.
- Create Stock Entry.
- Mutate Stock Ledger.
- Create Stock Reconciliation.
- Increase stock.
- Create or submit any ERPNext return, accounting, or stock document.
- Expose native ERPNext routes.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.
- Expose valuation, accounting, billing, payment, tax, margin, profit, rate, amount, price, cost, refund, credit, or commercial fields.

The purpose is to define how Warehouse should capture physical customer return intake evidence before any later runtime phase is considered.

## 2. Current Warehouse Context

Warehouse Console now has controlled execution-readiness foundations for inbound and outbound operations:

- W15C defines inbound receiving workflow design.
- W15C3 adds custom Warehouse Receiving Task draft/save behavior.
- W15C4 adds custom Receiving Task manager decisions.
- W15C5 defines a Purchase Receipt draft policy, while Purchase Receipt draft creation and submission remain blocked until later approval.
- W15D defines outbound picking and dispatch workflow design.
- W15D3 adds custom Warehouse Picking Task draft evidence saving.
- W15D4 adds custom Picking Task manager decisions.
- W15D5 defines dispatch handoff and Delivery Note policy, while Delivery Note draft creation and submission remain blocked.

Customer returns are not implemented yet. Warehouse Console must not mutate stock for customer returns. No Sales Return, Credit Note, return Delivery Note, Stock Entry, Stock Ledger mutation, or Stock Reconciliation exists from Warehouse Console.

## 3. Business Flow In Plain English

A customer return starts with the customer relationship, not with Warehouse stock posting.

A practical daily flow should be:

1. Customer reports or returns goods through Sales, customer service, or an approved return channel.
2. Sales owns the customer relationship and return authorization.
3. Sales owns refund, credit, replacement, customer communication, and customer-facing promise decisions.
4. Warehouse receives physical returned goods only after an approved or intended return intake context exists.
5. Warehouse records physical intake evidence.
6. Warehouse confirms item identity.
7. Warehouse counts returned quantity.
8. Warehouse inspects condition.
9. Warehouse records damage, repair, quarantine, scrap, or rejection evidence.
10. Warehouse Manager reviews the intake and chooses an internal return posture.
11. Sales/Admin/Finance owns any commercial documents, customer credit/refund decisions, and ERPNext document governance.
12. ERPNext remains the system of record for any eventual stock, customer, or accounting document.

The Warehouse return workflow should guide evidence and disposition, not silently update stock.

## 4. Customer Return Entry Sources

Possible future entry sources:

- Sales-approved return request.
- Delivery Note reference text, if later visible as safe text only.
- Sales Invoice reference text, if later visible as safe text only.
- Customer claim without document reference, requiring Sales validation.
- Warranty or repair request.
- Damaged delivery claim.
- Wrong item claim.
- Replacement or exchange request.

W15E1 does not approve native Delivery Note, Sales Invoice, Credit Note, or Sales Return route links. References should be plain text/status only until native route containment and role policy are approved.

## 5. Warehouse-Owned Steps

Warehouse owns physical evidence and warehouse-side posture.

Warehouse-owned steps:

- Physical intake check.
- Item identity confirmation.
- Quantity count.
- Condition inspection.
- Photo or evidence reference, later if supported.
- Quarantine tagging as a custom task state first.
- Damage, repair, scrap, or rejection evidence capture.
- Manager review state.
- Return disposition recommendation.

Warehouse does not own customer credit, refund, replacement promise, customer notification, or accounting outcome.

## 6. Sales/Admin/Finance-Owned Steps

Sales/Admin/Finance owns customer and commercial governance.

Sales/Admin/Finance-owned steps:

- Customer authorization.
- Customer notification.
- Refund policy.
- Credit policy.
- Replacement policy.
- Sales Return governance.
- Credit Note governance.
- Return Delivery Note governance.
- Accounting document governance.
- Commercial terms.
- Native ERPNext document creation and submission, if policy allows later.

Warehouse should escalate customer-facing or commercial return decisions to Sales/Admin/Finance instead of duplicating those workflows.

## 7. Recommended W15E Default

Recommended safest default:

- Warehouse creates or updates only custom Customer Return Intake records.
- No stock is increased.
- No Sales Return is created.
- No Credit Note is created.
- No return Delivery Note is mutated.
- No Stock Entry is created.
- No Stock Ledger entry is created.
- Restock, quarantine, repair, scrap, and reject decisions remain internal task states until later policy.

This keeps Warehouse focused on physical return evidence and avoids crossing into customer, accounting, and stock-posting decisions before governance is ready.

## 8. Proposed Future Custom Records

Design only. Do not implement in W15E1.

Potential parent record:

- `Warehouse Customer Return Intake`.

Possible parent fields:

- `customer`.
- `sales_order_reference_text`.
- `delivery_note_reference_text`.
- `sales_invoice_reference_text`.
- `return_authorization_reference`.
- `intake_status`.
- `warehouse`.
- `received_by`.
- `received_at`.
- `inspection_status`.
- `disposition`.
- `evidence_reference`.
- `manager_decision`.
- `sales_escalation_reference`.
- `notes`.
- Child table `lines`.
- Child table `events`.

Potential child line record:

- `Warehouse Customer Return Intake Line`.

Possible line fields:

- `item_code`.
- `item_name`.
- `returned_qty`.
- `accepted_qty`.
- `damaged_qty`.
- `quarantine_qty`.
- `repair_qty`.
- `scrap_candidate_qty`.
- `rejected_qty`.
- `condition_grade`.
- `disposition`.
- `evidence_reference`.
- `uom`.

Potential event record:

- `Warehouse Customer Return Intake Event`.

Possible event fields:

- `event_type`.
- `event_label`.
- `event_by`.
- `event_at`.
- `request_id`.
- `previous_status`.
- `next_status`.
- `details_json`.

These records must not include valuation, accounting, refund, credit, rate, amount, tax, margin, profit, cost, payment, billing, or native route fields.

## 9. Status Model

Future custom Customer Return Intake statuses:

- `Intake Draft`.
- `Received For Inspection`.
- `Inspection In Progress`.
- `Submitted For Manager Review`.
- `Restock Review`.
- `Quarantine Review`.
- `Repair Review`.
- `Scrap Review`.
- `Escalated To Sales`.
- `Rejected / Return To Customer`.
- `Closed / Cancelled`.

Status meaning:

- `Intake Draft`: Warehouse has started a custom return intake record. No stock change.
- `Received For Inspection`: Physical goods are present for inspection. No stock change.
- `Inspection In Progress`: Warehouse is checking item identity, count, and condition. No stock change.
- `Submitted For Manager Review`: User evidence is ready for manager review. No stock change.
- `Restock Review`: Manager believes the item may be restockable, but stock is not increased.
- `Quarantine Review`: Item needs hold or quality review. No stock change.
- `Repair Review`: Item may need repair. No stock change.
- `Scrap Review`: Item may be a scrap or write-off candidate. No stock or accounting change.
- `Escalated To Sales`: Customer-facing decision needed. No customer notification from Warehouse.
- `Rejected / Return To Customer`: Warehouse recommends return rejection or send-back handling. No customer communication from Warehouse.
- `Closed / Cancelled`: Custom workflow is closed or cancelled. No ERPNext stock or accounting mutation.

## 10. Manager Decision Matrix

Future manager decisions:

- `request_recount` or `request_reinspection`.
- `approve_restock_candidate`.
- `mark_quarantine_review`.
- `mark_repair_review`.
- `mark_scrap_candidate`.
- `reject_return_intake`.
- `escalate_to_sales`.
- `close_intake`.

Decision examples:

- Count mismatch: request recount.
- Clean unopened goods: approve restock candidate, with no stock posting.
- Damaged goods: mark quarantine review or repair review.
- Unsafe or unusable goods: mark scrap/write-off candidate for Finance/Admin governance.
- Wrong item returned: reject return intake or escalate to Sales.
- Missing customer authorization: escalate to Sales.
- Customer-facing dispute: escalate to Sales.

These decisions do not post stock. They do not create Sales Return. They do not create Credit Note. They do not create return Delivery Note. They do not notify the customer.

## 11. Eligibility And Exclusion Rules

Eligibility for a future return intake:

- Actor has Warehouse access.
- Sales/customer context is visible or an explicit Sales approval/reference exists.
- Customer or return source is known.
- Item identity is known.
- Quantity is counted.
- Condition is recorded.
- Damaged, repair, scrap, or quarantine posture has evidence reference.
- Manager approval exists before any restock recommendation.
- Request idempotency is enforced for future backend writes.

Exclude or block by default:

- Unknown customer without Sales validation.
- Unknown item.
- Missing return authorization when policy requires authorization.
- Damaged goods from normal restock.
- Quarantine goods from normal restock.
- Scrap/write-off candidate without manager plus Finance/Admin approval.
- Any commercial, valuation, accounting, refund, credit, or payment fields in Warehouse UI or payload.
- Any native ERPNext route.
- Any client-trusted return document line mapping.
- Any attempt to increase stock from the custom intake shell.

## 12. Future ERPNext Document Mapping

Future policy may need to consider ERPNext documents such as:

- Sales Return.
- Return Delivery Note.
- Credit Note.
- Stock Entry.
- Stock Reconciliation.

W15E1 does not approve creating or submitting any of those documents.

If a later draft/request is allowed, it should be request-only first and governed by Sales/Admin/Finance. Warehouse should provide physical evidence and disposition recommendation. ERPNext documents should remain system-of-record documents controlled by an approved policy.

Any future ERPNext document mapping must be server-side, role-gated, idempotent, auditable, and blocked from native route escape for normal Warehouse users.

## 13. Evidence Requirements

Future customer return intake evidence should include:

- Return authorization reference.
- Customer/source reference.
- Sales approval reference when required.
- Item identity.
- Quantity count.
- Condition grade.
- Damaged evidence reference.
- Repair evidence reference.
- Scrap evidence reference.
- Quarantine evidence reference.
- Manager event.
- Sales escalation reference when customer-facing.
- Idempotency request id for future backend operations.

Evidence should be bounded, business-safe, and attached to custom Warehouse records or approved event records. It must not include commercial amounts, refund amounts, rates, tax, accounts, GL, margin, profit, payment, or billing values.

## 14. Native Route And Commercial Containment

W15E1 explicitly blocks native route exposure from Warehouse customer return surfaces.

Blocked route targets:

- `/app`.
- `/desk/Form`.
- `/desk/List`.
- `/desk/Report`.
- `/desk/query-report`.
- Sales Invoice native link.
- Delivery Note native link.
- Credit Note native link.
- Sales Return native link.
- Stock Ledger native link.
- Stock Balance native link.
- Stock Reconciliation native link.

Blocked commercial/accounting fields:

- Valuation.
- Valuation rate.
- Rate.
- Amount.
- Base amount.
- Tax.
- Account.
- GL.
- Margin.
- Profit.
- Cost.
- Payment.
- Refund detail.
- Credit amount.
- Billing detail.
- Customer commercial terms.

If references are shown later, they should be plain text/status only until native-submit and native-route containment is approved.

## 15. Role Model

### Warehouse User

Warehouse User owns physical intake, count, and evidence.

Allowed future responsibilities:

- Start custom return intake.
- Record item identity.
- Record quantity count.
- Record condition grade.
- Record evidence reference.
- Submit intake for manager review.

Forbidden:

- Decide customer refund or credit.
- Create Sales Return.
- Create Credit Note.
- Create return Delivery Note.
- Increase stock.
- Post stock.
- Notify customer.

### Warehouse Manager / Stock Manager

Warehouse Manager and Stock Manager own internal disposition decisions.

Allowed future responsibilities:

- Request recount or reinspection.
- Approve restock candidate as an internal state only.
- Mark quarantine review.
- Mark repair review.
- Mark scrap/write-off candidate.
- Reject return intake as an internal recommendation.
- Escalate to Sales.
- Close intake.

Forbidden by W15E1:

- Create or submit ERPNext return documents.
- Increase stock.
- Override Sales, Finance, or Admin customer/commercial decisions.

### Sales User / Sales Manager

Sales owns customer authorization, notification, and customer-facing decisions.

Responsibilities:

- Return authorization.
- Customer communication.
- Replacement decision.
- Customer-facing promise and dispute resolution.
- Sales-side return governance.

### Finance/Admin

Finance/Admin owns credit, refund, accounting, write-off, and document governance.

Responsibilities:

- Credit/refund policy.
- Accounting document governance.
- Scrap/write-off approval.
- ERPNext return document ownership if later approved.

### System/Admin

System/Admin owns policy configuration.

Responsibilities:

- Role configuration.
- Return authorization policy.
- Warehouse scope policy.
- Evidence requirements.
- Native route containment policy.
- Future document governance configuration.

### Procurement

Procurement is generally not involved in customer returns. Procurement may be involved only if the return exposes a supplier issue that triggers a separate supplier return or sourcing follow-up.

## 16. Test Plan For Future Implementation

Future implementation tests must verify:

- No stock mutation.
- No Sales Return creation.
- No Credit Note creation.
- No return Delivery Note creation.
- No Stock Entry creation.
- No Stock Ledger mutation.
- No Stock Reconciliation mutation.
- No native routes in payload or UI.
- No valuation/commercial/accounting exposure.
- Sales approval required when return authorization policy requires it.
- Damaged goods require evidence.
- Quarantine posture requires evidence.
- Repair posture requires evidence.
- Scrap/write-off candidate requires evidence and manager decision.
- Manager-only disposition decisions.
- Warehouse User denied manager decisions.
- Sales/Finance/Admin-only decisions are not exposed to Warehouse roles.
- Idempotency prevents duplicate intake records or duplicate manager events.
- Safe payload flags remain false for stock and commercial effects.

## 17. Open Owner Decisions

Owner decisions needed before runtime implementation:

- Is Sales approval required before Warehouse can intake any customer return?
- Can Warehouse intake without original Sales Order or Delivery Note reference?
- Who decides restock versus quarantine versus repair versus scrap?
- Is Finance/Admin approval required for scrap/write-off?
- Can Warehouse see reference text for Sales Invoice or Delivery Note?
- Is repair workflow in scope?
- Should customer return create a Sales/Admin queue?
- When, if ever, can stock be increased from a customer return?
- Should customer return intake require photo evidence?
- Should return authorization be mandatory for every customer return?
- Which warehouses may receive customer returns?
- Who closes or cancels customer return intake tasks?

## 18. Recommended Next Phase

Recommended W15E2 path:

- Either create a UI shell for Customer Return Intake with no backend writes, or create a detailed custom Customer Return Intake backend design before implementation.
- If backend implementation is chosen later, create only custom Warehouse Customer Return Intake records first.
- Do not implement ERPNext return documents until owner, Security/Stability, Sales, Finance/Admin, and operational decisions are resolved.

W15E2 should not create Sales Return, Credit Note, return Delivery Note, Stock Entry, Stock Ledger mutation, Stock Reconciliation, stock increase, customer notification, native ERPNext route escape, or valuation/accounting/commercial exposure.
