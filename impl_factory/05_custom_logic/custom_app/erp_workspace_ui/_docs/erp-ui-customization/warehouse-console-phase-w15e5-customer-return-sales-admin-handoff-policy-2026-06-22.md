# Warehouse Console Phase W15E5 Customer Return Sales/Admin Handoff Policy

Date: 2026-06-22

Status: docs-only Warehouse policy and design gate. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W15E1 Customer Return Workflow Design.
- W15E2 Customer Return Intake overview UI shell.
- W15E3 custom Warehouse Customer Return Intake draft backend.
- W15E4 custom Warehouse Customer Return Intake manager decisions.

## 1. Title And Scope

W15E5 defines the policy boundary for handing customer return intake decisions from Warehouse to Sales, Admin, and Finance.

This is a design gate only. It does not approve runtime implementation. It does not approve Sales Return creation. It does not approve Credit Note creation. It does not approve Stock Entry creation. It does not approve stock increase. It does not approve customer notification.

The purpose is to separate Warehouse physical return disposition from customer-facing, commercial, accounting, and ERPNext stock document governance before any future handoff implementation is considered.

W15E5 must not:

- Create Sales Return.
- Create Credit Note.
- Create return Delivery Note.
- Create Stock Entry.
- Create Stock Reconciliation.
- Mutate Stock Ledger.
- Increase stock.
- Post stock.
- Update Sales Order.
- Notify customer.
- Send email.
- Open portal access.
- Expose native ERPNext routes.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.
- Expose valuation, accounting, billing, payment, tax, margin, profit, rate, amount, price, cost, refund, credit, or commercial fields.

## 2. Current W15E State

The current customer-return track is deliberately limited to custom Warehouse records.

Current state:

- W15E1 defines the customer return workflow boundary.
- W15E2 adds a UI-only shell on Warehouse Overview for future return intake posture.
- W15E3 adds custom `Warehouse Customer Return Intake` draft evidence saving.
- W15E4 adds custom `Warehouse Customer Return Intake` manager decisions.
- W15E4 decisions update only custom intake status and event rows.
- No Sales Return exists from Warehouse Console.
- No Credit Note exists from Warehouse Console.
- No Stock Entry exists from Warehouse Console.
- No Stock Ledger mutation exists from Warehouse Console.
- No customer notification exists from Warehouse Console.

Current W15E4 manager decisions such as `Restock Candidate`, `Repair Candidate`, `Scrap Candidate`, `Quarantine Review`, `Rejected Intake`, and `Sales Escalation` are internal Warehouse disposition posture only. They are not stock movements, customer decisions, or accounting decisions.

## 3. Business Flow In Plain English

A customer return has two different sides.

Warehouse handles the physical side:

- Did goods arrive back at the warehouse?
- Which customer and return authorization is this related to?
- Which item was returned?
- How many were returned?
- What condition are the goods in?
- Are goods clean, damaged, repairable, quarantined, scrap candidate, or rejected?
- What evidence supports the condition?

Sales, Admin, and Finance handle the customer and business side:

- Is this return authorized?
- Does the customer get replacement, credit, refund, or rejection?
- Should the customer be notified?
- Should Sales Order or customer promise be changed?
- Should a Sales Return, Credit Note, Stock Entry, or accounting document be prepared?
- Who approves commercial or accounting consequences?

The safest next step after Warehouse Manager disposition is not a stock document. The safest next step is a controlled handoff request or status for Sales/Admin/Finance review.

## 4. Handoff Policy

W15E5 defines handoff as a request/status transition only.

Handoff means:

- Warehouse has recorded physical return evidence.
- Warehouse Manager or Stock Manager has reviewed the intake.
- The return now needs Sales, Admin, or Finance ownership for customer or document decisions.
- The handoff carries safe operational facts and references.

Handoff does not mean:

- Sales Return was created.
- Credit Note was created.
- Stock Entry was created.
- Stock was increased.
- Customer was notified.
- Refund or credit was approved.
- Write-off was approved.
- ERPNext document was submitted.

Visible Warehouse copy should use careful language such as `Sales/Admin handoff requested`, `Needs Sales review`, `Finance/Admin decision needed`, or `Return disposition ready for business review`.

Visible Warehouse copy must not use `Refunded`, `Credited`, `Returned to stock`, `Stock updated`, `Sales Return created`, `Credit Note created`, or `Customer notified` unless a later approved ERPNext process has actually completed that event.

## 5. Recommended Default

The recommended default is request-only handoff.

Warehouse should create or update a custom request/status that tells Sales/Admin/Finance what business decision is needed. Warehouse should not create ERPNext customer, accounting, or stock documents.

Why this is safest:

- Warehouse stays focused on physical evidence and condition.
- Sales keeps ownership of customer communication and customer promise.
- Finance/Admin keeps ownership of refund, credit, write-off, and accounting treatment.
- Native ERPNext submit bypass risk stays lower.
- Warehouse users do not receive native document routes or draft document handles.
- Stock is not increased from a return until approved document governance exists.

This default matches the outbound dispatch approach: request or handoff first, ERPNext document policy later.

## 6. Possible Future Handoff Records

Design only. Do not implement in W15E5.

Recommended future parent record:

- `Warehouse Customer Return Handoff Request`.

Possible parent fields:

- `customer_return_intake`.
- `customer`.
- `warehouse`.
- `handoff_status`.
- `handoff_type`.
- `manager_decision`.
- `return_authorization_reference`.
- `sales_order_reference_text`.
- `delivery_note_reference_text`.
- `sales_invoice_reference_text`.
- `sales_escalation_reference`.
- `finance_escalation_reference`.
- `handoff_note`.
- `source_payload_hash`.
- `policy_version`.
- `line_count`.
- `total_returned_qty`.
- `request_id`.
- `requested_by`.
- `requested_at`.
- Child table `lines`.
- Child table `events`.

Possible child line record:

- `Warehouse Customer Return Handoff Request Line`.

Possible line fields:

- `intake_line_reference` as plain text only.
- `item_code`.
- `item_name`.
- `warehouse`.
- `returned_qty`.
- `accepted_for_intake_qty`.
- `damaged_qty`.
- `quarantine_qty`.
- `repair_qty`.
- `scrap_candidate_qty`.
- `rejected_qty`.
- `condition_grade`.
- `disposition`.
- `evidence_reference` as inert text only.
- `uom`.

Possible event record:

- `Warehouse Customer Return Handoff Request Event`.

Possible event fields:

- `event_type`.
- `event_label`.
- `event_by`.
- `event_at`.
- `request_id`.
- `details_json`.

These records must not include native route, Link, Dynamic Link, Attach, HTML, valuation, accounting, refund, credit, rate, amount, tax, margin, profit, cost, payment, billing, email, portal, or customer notification fields unless a later security review explicitly approves that specific field.

## 7. Handoff Types

Future handoff types should be explicit and business-owned.

Recommended handoff types:

- `sales_authorization_review`: Sales must validate return authorization or customer promise.
- `customer_resolution_review`: Sales must decide replacement, rejection, or customer communication.
- `finance_credit_review`: Finance/Admin must decide credit, refund, or write-off policy.
- `stock_governance_review`: Admin/Stock Manager must decide if and how ERPNext stock document processing may occur later.
- `quarantine_quality_review`: Quality/Admin must decide quarantine disposition.
- `repair_review`: Repair/Admin must decide repair process.
- `scrap_writeoff_review`: Finance/Admin must decide scrap or write-off process.

Warehouse should not use generic `approve return` language because approval could be confused with customer refund, stock increase, or ERPNext return document creation.

## 8. Eligibility Rules For Future Handoff Request

Any future handoff request method must require all of these conditions:

- A custom `Warehouse Customer Return Intake` exists.
- The intake is visible to the current Warehouse context.
- The intake has line evidence.
- The intake has a manager-reviewed state.
- The manager state is one of the approved handoff source states.
- Customer is present.
- Warehouse is present and visible.
- Return authorization reference is present unless owner policy allows unauthorized intake escalation.
- Lines have item identity.
- Returned quantity is positive.
- Disposition quantities are server-validated.
- Exception lines have evidence or condition note.
- Handoff type is allowlisted.
- Request idempotency is enforced.
- Audit event is appended.
- Returned payload keeps all stock/customer/accounting/commercial side-effect flags false.

The future method must reject client-supplied trusted ERPNext document fields. Sales Return, Credit Note, Stock Entry, Stock Ledger, Stock Reconciliation, Sales Order, customer notification, accounting, and valuation fields must not be accepted from Warehouse payload.

## 9. Allowed Source States

Potential allowed source states for a handoff request:

- `Restock Candidate`.
- `Quarantine Review`.
- `Repair Candidate`.
- `Scrap Candidate`.
- `Rejected Intake`.
- `Sales Escalation`.

State meaning:

- `Restock Candidate`: Warehouse evidence suggests item might be restockable. Stock is not increased.
- `Quarantine Review`: Warehouse evidence indicates hold or quality review. Stock is not posted.
- `Repair Candidate`: Warehouse evidence indicates repair review. No repair document or stock movement is created.
- `Scrap Candidate`: Warehouse evidence indicates possible scrap/write-off. Finance/Admin must decide. No accounting mutation occurs.
- `Rejected Intake`: Warehouse recommends rejection or return-to-customer handling. Sales owns customer communication.
