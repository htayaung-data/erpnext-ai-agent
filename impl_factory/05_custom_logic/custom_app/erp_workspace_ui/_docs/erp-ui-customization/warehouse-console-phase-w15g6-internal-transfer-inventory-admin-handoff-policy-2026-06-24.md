# Warehouse Console Phase W15G6 Internal Transfer Inventory/Admin Handoff Policy

Date: 2026-06-24

Status: docs-only Warehouse policy and design gate. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W15G1 Internal Transfer Workflow Design.
- W15G2 Internal Transfer Candidate overview UI shell.
- W15G3 custom Warehouse Internal Transfer Candidate metadata.
- W15G4 custom Warehouse Internal Transfer Candidate draft backend.
- W15G5 custom Warehouse Internal Transfer Candidate manager decisions.

## 1. Title And Scope

W15G6 defines the policy boundary for handing internal-transfer candidate decisions from Warehouse to Inventory/Admin stock-document governance.

This is a design gate only. It does not approve runtime implementation. It does not approve Stock Entry draft creation. It does not approve Stock Entry submission. It does not approve stock movement, stock reservation, Stock Ledger mutation, Stock Balance mutation, or Stock Reconciliation.

The purpose is to separate Warehouse physical transfer evidence and manager posture from Inventory/Admin ownership of ERPNext stock document governance before any future handoff implementation is considered.

W15G6 must not:

- Create Stock Entry.
- Save Stock Entry.
- Submit Stock Entry.
- Cancel Stock Entry.
- Amend Stock Entry.
- Create Stock Reconciliation.
- Mutate Stock Ledger.
- Mutate Stock Balance.
- Create Stock Reservation.
- Reserve stock.
- Unreserve stock.
- Move stock between warehouses.
- Post stock.
- Update Sales Order, Purchase Order, Delivery Note, Purchase Receipt, Purchase Invoice, Pick List, or Material Request.
- Trigger customer notification.
- Trigger supplier notification.
- Send email.
- Open portal access.
- Expose native ERPNext routes.
- Expose `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report` native route patterns.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.
- Expose valuation, accounting, billing, payment, tax, landed cost, margin, profit, rate, amount, price, cost, debit, credit, payable, GL, or commercial fields.

## 2. Current W15G State

The current internal-transfer track is deliberately limited to custom Warehouse evidence and manager posture.

Current state:

- W15G1 defines the internal transfer workflow boundary.
- W15G2 adds a UI-only shell on Warehouse Overview for future internal transfer candidate posture.
- W15G3 adds custom `Warehouse Internal Transfer Candidate` metadata.
- W15G4 adds custom `Warehouse Internal Transfer Candidate` draft evidence saving.
- W15G5 adds custom `Warehouse Internal Transfer Candidate` manager decisions.
- W15G5 decisions update only custom candidate status and event rows.
- No Stock Entry exists from Warehouse Console.
- No stock moves from Warehouse Console.
- No Stock Ledger, Stock Balance, Stock Reconciliation, or Stock Reservation mutation exists from Warehouse Console.
- No native Stock Entry route is exposed from Warehouse Console.

Current W15G5 manager decisions such as `Transfer Candidate`, `Quarantine Review`, `Inventory/Admin Review`, `Rejected`, `Cancelled`, `Closed`, and `Recount Requested` are internal Warehouse posture only. They are not Stock Entry approval, stock movement, reservation, accounting, or ERPNext document creation.

## 3. Business Flow In Plain English

An internal transfer has two different sides.

Warehouse handles the physical and operational side:

- Which item may need to move?
- Which source warehouse and target warehouse are involved?
- What quantity was requested, counted, and recommended as transfer candidate?
- Is there any shortage, damage, quarantine, blocked target, or exception posture?
- What evidence supports the transfer candidate posture?
- What manager recommendation was recorded?

Inventory/Admin handles the stock-document governance side:

- Is this transfer allowed by warehouse policy?
- Is the target warehouse valid for the item and condition?
- Is the source quantity eligible to move?
- Are quarantine, quality, serial, batch, reservation, or compliance rules involved?
- Should a Stock Entry draft/request ever be prepared?
- Who can create, review, submit, cancel, or amend any eventual ERPNext stock document?
- How is native-submit bypass contained?

The safest next step after Warehouse Manager disposition is not Stock Entry draft creation. The safest next step is a controlled request/status handoff for Inventory/Admin review.

## 4. Handoff Policy

W15G6 defines handoff as a request/status transition only.

Handoff means:

- Warehouse has recorded physical transfer evidence.
- Warehouse Manager or Stock Manager has reviewed the candidate.
- The candidate now needs Inventory/Admin policy ownership.
- The handoff carries safe operational facts and plain text references.

Handoff does not mean:

- Stock was moved.
- Stock Entry was created.
- Stock Entry was submitted.
- Stock Entry was cancelled or amended.
- Stock Ledger was mutated.
- Stock Balance was mutated.
- Stock Reservation was created.
- Stock Reconciliation was created.
- Source or target warehouse inventory changed.
- Inventory/Admin approved transfer execution.
- Native ERPNext route access was granted.

Visible Warehouse copy should use careful language such as `Inventory/Admin review requested`, `Stock document policy review needed`, `Transfer candidate only`, or `No stock moved`.

Visible Warehouse copy must not use `Transfer approved`, `Stock moved`, `Stock Entry created`, `Stock Entry submitted`, `Reservation created`, `Ledger updated`, or `Posted transfer` unless a later approved ERPNext process has actually completed that event.

## 5. Recommended Default

The recommended default is request-only Inventory/Admin handoff.

Warehouse should create or update a custom request/status that tells Inventory/Admin what stock-document decision is needed. Warehouse should not create ERPNext Stock Entry drafts or submitted stock documents.

Why this is safest:

- Warehouse stays focused on physical evidence and transfer intent.
- Warehouse Manager recommendation stays separate from ERPNext stock movement.
- Inventory/Admin keeps ownership of stock-document governance.
- Native ERPNext submit bypass risk stays lower.
- Warehouse users do not receive native Stock Entry routes or draft document handles.
- Stock is not moved until approved document governance exists.

This default matches the established W15 pattern: evidence first, manager posture second, request-only handoff third, ERPNext document policy later.

## 6. Possible Future Handoff Records

Design only. Do not implement in W15G6.

Recommended future parent record:

- `Warehouse Internal Transfer Handoff Request`.

Possible parent fields:

- `internal_transfer_candidate`.
- `source_context`.
- `source_reference_text`.
- `source_warehouse`.
- `target_warehouse`.
- `handoff_status`.
- `handoff_type`.
- `manager_decision`.
- `inventory_admin_escalation_reference`.
- `quarantine_review_reference`.
- `handoff_note`.
- `source_payload_hash`.
- `policy_version`.
- `line_count`.
- `total_candidate_qty`.
- `request_id`.
- `requested_by`.
- `requested_at`.
- Child table `lines`.
- Child table `events`.

Possible child line record:

- `Warehouse Internal Transfer Handoff Request Line`.

Possible line fields:

- `candidate_line_reference` as plain text only.
- `item_code`.
- `item_name`.
- `source_warehouse`.
- `target_warehouse`.
- `requested_qty`.
- `counted_qty`.
- `transfer_candidate_qty`.
- `blocked_qty`.
- `quarantine_qty`.
- `damaged_qty`.
- `short_qty`.
- `condition_grade`.
- `reason_code`.
- `evidence_reference` as inert text only.
- `uom`.

Possible event record:

- `Warehouse Internal Transfer Handoff Request Event`.

Possible event fields:

- `event_type`.
- `event_label`.
- `event_by`.
- `event_at`.
- `request_id`.
- `details_json`.

These records must not include native route, Link, Dynamic Link, Attach, Attach Image, HTML, Button, valuation, accounting, payable, debit, credit, rate, amount, tax, margin, profit, cost, landed cost, payment, billing, GL, email, portal, customer notification, supplier notification, Stock Entry link, Stock Ledger link, Stock Balance link, Stock Reservation link, or Stock Reconciliation link fields unless a later security review explicitly approves that specific field.

## 7. Handoff Types

Future handoff types should be explicit and business-owned.

Recommended handoff types:

- `stock_document_policy_review`: Inventory/Admin must review whether any future stock document path is allowed. Request only; no Stock Entry is created.
- `source_target_policy_review`: Inventory/Admin must review whether the source and target warehouse pair is valid. Request only; no warehouse inventory changes.
- `quarantine_quality_review`: Quality/Admin must review quarantine, damaged, blocked, or restricted stock posture. Request only; no stock movement occurs.
- `reservation_policy_review`: Inventory/Admin must review whether stock reservation policy is relevant. Request only; no reservation is created.
- `serial_batch_policy_review`: Inventory/Admin must review serial or batch handling. Request only; no serial/batch movement is posted.
- `transfer_execution_review`: Inventory/Admin must review whether transfer execution should be prepared later. Request only; no Stock Entry draft or submission occurs.
- `close_or_cancel_review`: Inventory/Admin or manager must review close/cancel ownership. Request only; no ERPNext stock document is cancelled or amended.

Raw handoff keys must not be shown to owner-facing UI. Future UI should render business labels such as `Stock document policy review`, `Source/target policy review`, and `Transfer execution review`, each with `request only` and `no stock moved` context.

Warehouse should not use generic `approve transfer` language because approval could be confused with stock movement, Stock Entry creation, or Stock Ledger posting.

## 8. Eligibility Rules For Future Handoff Request

A future W15G7/W15G8 handoff implementation should require:

- Existing custom `Warehouse Internal Transfer Candidate`.
- Candidate status must be a manager-reviewed state such as `Transfer Candidate`, `Inventory/Admin Review`, `Quarantine Review`, `Rejected`, `Cancelled`, or `Closed`, depending on handoff type.
- Candidate must have source warehouse and target warehouse.
- Source and target warehouses must be different.
- Candidate must have line evidence.
- Candidate lines must be derived from the custom candidate record, not arbitrary client rows.
- Transfer candidate quantity must be non-negative and policy-valid.
- Blocked, damaged, quarantine, and short posture must be carried as evidence.
- Handoff note must be required.
- Request id must be required.
- Idempotency must reject changed-payload reuse and cross-candidate reuse.
- Payload must return false stock-effect flags.
- Response must not include native route links.
- Response must not include valuation, accounting, commercial, rate, amount, tax, GL, cost, margin, or profit fields.

The future service should not trust client-supplied line ownership, warehouse ownership, native route references, stock document identifiers, or stock movement status.

## 9. Source-State To Handoff-Type Mapping

Recommended source-state mapping for future implementation:

- `Transfer Candidate` may request:
  - `stock_document_policy_review`.
  - `source_target_policy_review`.
  - `transfer_execution_review`.
- `Inventory/Admin Review` may request:
  - `stock_document_policy_review`.
  - `source_target_policy_review`.
  - `reservation_policy_review`.
  - `serial_batch_policy_review`.
  - `transfer_execution_review`.
- `Quarantine Review` may request:
  - `quarantine_quality_review`.
  - `stock_document_policy_review`.
- `Rejected` may request:
  - `close_or_cancel_review`.
- `Cancelled` may request:
  - `close_or_cancel_review`.
- `Closed` normally should not create new handoff requests unless owner policy explicitly allows historical review.
- `Draft`, `Count In Progress`, `Submitted For Review`, and `Recount Requested` should not create Inventory/Admin handoff requests until manager review is complete.

The exact mapping remains an owner/security decision before runtime.

## 10. Role Ownership

Recommended role ownership:

- Warehouse User: physical transfer intent and count evidence only.
- Stock User: physical transfer intent and count evidence only where warehouse access allows.
- Warehouse Manager: internal transfer recommendation and handoff request under policy.
- Stock Manager: internal transfer recommendation and Inventory/Admin handoff request under policy.
- System Manager: policy/admin override.
- Inventory/Admin: ERPNext stock document governance and native-submit containment.
- Sales: not involved unless transfer impacts customer dispatch promise.
- Procurement: not involved unless transfer is tied to receiving dispute or supplier return.
- Finance/Admin: not involved unless later accounting/write-off policy applies.

Warehouse Manager and Stock Manager may request review. They should not create, save, submit, cancel, or amend ERPNext Stock Entry through Warehouse Console in W15G6.

## 11. Evidence Requirements

Future handoff request should carry:

- Candidate id.
- Source context.
- Source reference text.
- Source warehouse.
- Target warehouse.
- Transfer reason.
- Manager decision.
- Handoff type.
- Handoff note.
- Line item code and item name.
- Requested quantity.
- Counted quantity.
- Transfer candidate quantity.
- Blocked, quarantine, damaged, and short quantities.
- Condition grade.
- Reason code.
- Evidence reference as plain text only.
- UOM.
- Request id.
- Source payload hash.
- Policy version.

Evidence references must remain inert text until attachment/file policy is separately approved.

## 12. Native Route Boundary

W15G6 does not approve native ERPNext route exposure.

Blocked native route patterns:

- `/app`
- `/desk/Form`
- `/desk/List`
- `/desk/Report`
- `/desk/query-report`

Blocked native document route examples:

- Stock Entry form/list/report.
- Stock Ledger report.
- Stock Balance report.
- Stock Reconciliation form/list/report.
- Stock Reservation form/list/report.
- Pick List form/list/report.
- Delivery Note form/list/report.
- Purchase Receipt form/list/report.
- Sales Order form/list/report.
- Purchase Order form/list/report.

Future references, if shown, should be plain text/status only unless native-route containment is separately approved by Security/Stability.

## 13. Stock Document Boundary

W15G6 explicitly blocks:

- Stock Entry draft creation.
- Stock Entry save.
- Stock Entry submit.
- Stock Entry cancel.
- Stock Entry amend.
- Stock Entry delete.
- Stock Entry route exposure.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Reconciliation creation or mutation.
- Stock Reservation creation or mutation.
- Reserve/unreserve actions.
- Stock posting.
- Any direct ERPNext stock movement from Warehouse Console.

If a later phase considers Stock Entry draft creation, it must be a new policy gate after owner approval and Security/Stability review. It must also define native-submit containment, role ownership, draft reference visibility, audit, and protected gate requirements.

## 14. Valuation, Accounting, And Commercial Boundary

Warehouse UI, payloads, custom records, and events must not expose:

- Valuation rate.
- Stock value.
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

Internal transfer evidence should stay operational: item, source warehouse, target warehouse, quantity, condition, reason, evidence, and review posture.

## 15. Open Owner Decisions Before Runtime

Before W15G7/W15G8 runtime, owner/security decisions must resolve:

- Which W15G5 states can create each handoff type.
- Whether Warehouse Manager can request Inventory/Admin review directly or Stock Manager/System Manager must own it.
- Whether any handoff type should be Inventory/Admin-only.
- Whether source and target warehouse pair restrictions are needed.
- Whether quarantine/restricted stock can be included in handoff requests.
- Whether serial/batch items are in scope.
- Whether reservation policy is ever allowed from Warehouse Console.
- Whether any Stock Entry draft can ever be created from Warehouse Console.
- Whether Stock Entry draft references can be visible to Warehouse users.
- Whether references remain plain text/status only or can become native links later.
- Whether evidence attachments are allowed later.
- Who can close or cancel internal transfer candidates and handoff requests.
- How native-submit bypass is contained.
- Which protected gates are mandatory before live alignment.

Default recommendations:

- Keep handoff request-only.
- Keep references plain text/status only.
- Keep Stock Entry draft creation blocked.
- Keep Stock Entry submission outside Warehouse Console.
- Keep reservation disabled.
- Require manager note for every handoff request.
- Require idempotency for every handoff request.

## 16. Future Implementation Test Requirements

Any future runtime implementation must include tests proving:

- Warehouse User and Stock User cannot bypass manager handoff policy if manager-only is chosen.
- Manager role gate is server-side.
- Source candidate is custom `Warehouse Internal Transfer Candidate`.
- Lines are derived from source candidate, not arbitrary client rows.
- Source state to handoff type mapping is enforced.
- Handoff note is required.
- Request id is required.
- Same request returns idempotently.
- Changed payload with same request rejects.
- Cross-candidate request id reuse rejects.
- No Stock Entry is created.
- No Stock Entry is saved.
- No Stock Entry is submitted.
- No Stock Entry is cancelled or amended.
- No Stock Ledger mutation occurs.
- No Stock Balance mutation occurs.
- No Stock Reconciliation mutation occurs.
- No Stock Reservation mutation occurs.
- No stock movement or posting occurs.
- No native route is exposed.
- No valuation/accounting/commercial fields are exposed.
- No Sales or Procurement runtime behavior changes.
- No notification, email, portal, or external action occurs.

## 17. Acceptance Criteria For W15G6

W15G6 is acceptable when:

- It remains docs-only.
- It defines Inventory/Admin handoff as request/status only.
- It confirms W15G5 manager decisions remain internal Warehouse posture only.
- It blocks Stock Entry draft creation and Stock Entry submission.
- It blocks stock movement, Stock Ledger, Stock Balance, Stock Reconciliation, and Stock Reservation mutation.
- It blocks native ERPNext routes.
- It blocks valuation, accounting, commercial, Sales, Procurement, notification, email, and portal behavior.
- It captures open owner decisions before runtime.
- It updates README roadmap/status only.

## 18. Final Boundary Statement

W15G6 is only a policy and design artifact for future internal transfer Inventory/Admin handoff planning.

It does not create runtime behavior. It does not create backend methods. It does not create DocTypes. It does not change smokes or tests. It does not align live files. It does not restart services. It does not commit or push by itself.

No Stock Entry draft or submission is approved. No stock movement is approved. No Stock Ledger, Stock Balance, Stock Reconciliation, or Stock Reservation mutation is approved. No native ERPNext route exposure is approved. No valuation/accounting/commercial exposure is approved.
