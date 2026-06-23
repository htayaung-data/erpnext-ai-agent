# Warehouse Console Phase W15F5 Supplier Return Procurement/Admin Handoff Policy

Date: 2026-06-23

Status: docs-only Warehouse policy and design gate. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W15F1 Supplier Return Workflow Design.
- W15F2 Supplier Return Candidate overview UI shell.
- W15F3 custom Warehouse Supplier Return Candidate draft backend.
- W15F4 custom Warehouse Supplier Return Candidate manager decisions.

## 1. Title And Scope

W15F5 defines the policy boundary for handing supplier-return candidate decisions from Warehouse to Procurement, Finance/Admin, and later document governance.

This is a design gate only. It does not approve runtime implementation. It does not approve supplier notification. It does not approve return Purchase Receipt creation. It does not approve Purchase Invoice return or debit note creation. It does not approve Stock Entry creation. It does not approve stock movement, stock decrease, or stock posting.

The purpose is to separate Warehouse physical supplier-return evidence from supplier-facing, procurement, commercial, payable, accounting, and ERPNext stock document governance before any future handoff implementation is considered.

W15F5 must not:

- Create return Purchase Receipt.
- Create Purchase Invoice return or debit note.
- Create Stock Entry.
- Create Stock Reconciliation.
- Mutate Stock Ledger.
- Mutate Stock Balance.
- Decrease stock.
- Move stock to supplier.
- Update Purchase Order.
- Notify supplier.
- Send email.
- Open portal access.
- Expose native ERPNext routes.
- Change Procurement runtime behavior.
- Change Sales runtime behavior.
- Expose valuation, accounting, billing, payment, tax, landed cost, margin, profit, rate, amount, price, cost, debit, credit, payable, GL, or commercial fields.

## 2. Current W15F State

The current supplier-return track is deliberately limited to custom Warehouse evidence and manager posture.

Current state:

- W15F1 defines the supplier return workflow boundary.
- W15F2 adds a UI-only shell on Warehouse Overview for future supplier return candidate posture.
- W15F3 adds custom `Warehouse Supplier Return Candidate` draft evidence saving.
- W15F4 adds custom `Warehouse Supplier Return Candidate` manager decisions.
- W15F4 decisions update only custom candidate status and event rows.
- No supplier is notified from Warehouse Console.
- No return Purchase Receipt exists from Warehouse Console.
- No Purchase Invoice return or debit note exists from Warehouse Console.
- No Stock Entry exists from Warehouse Console.
- No Stock Ledger or Stock Balance mutation exists from Warehouse Console.

Current W15F4 manager decisions such as `Supplier Return Candidate`, `Procurement Escalation`, `Finance/Admin Escalation`, `Quarantine Review`, `Rejected Candidate`, and `Reinspection Requested` are internal Warehouse disposition posture only. They are not supplier approval, supplier communication, stock movement, payable adjustment, debit approval, or ERPNext document creation.

## 3. Business Flow In Plain English

A supplier return has two different sides.

Warehouse handles the physical side:

- Which goods may need to go back to a supplier?
- Which supplier/source reference is this related to?
- Which item and quantity are affected?
- What is the condition of the goods?
- Are goods damaged, wrong item, quarantined, supplier-return candidate, or rejected?
- What evidence supports the supplier-return posture?

Procurement, Finance/Admin, and later document governance handle the business side:

- Is the supplier return authorized?
- Should Procurement contact the supplier?
- Is there a supplier claim, replacement, supplier credit, or dispute?
- Is a Purchase Order correction needed?
- Is a debit note, payable adjustment, or accounting treatment needed?
- Should an ERPNext return or stock document be prepared later?
- Who approves supplier-facing and commercial consequences?

The safest next step after Warehouse Manager disposition is not supplier notification or a stock document. The safest next step is a controlled handoff request or status for Procurement/Admin/Finance review.

## 4. Handoff Policy

W15F5 defines handoff as a request/status transition only.

Handoff means:

- Warehouse has recorded physical supplier-return evidence.
- Warehouse Manager or Stock Manager has reviewed the candidate.
- The candidate now needs Procurement, Finance/Admin, quality, or document-policy ownership.
- The handoff carries safe operational facts and plain text references.

Handoff does not mean:

- Supplier was notified.
- Supplier accepted the return.
- Goods moved to supplier.
- Stock was decreased.
- Return Purchase Receipt was created.
- Purchase Invoice return or debit note was created.
- Stock Entry was created.
- Stock Ledger or Stock Balance was mutated.
- Purchase Order was updated.
- Debit, credit, payable adjustment, replacement, or commercial outcome was approved.

Visible Warehouse copy should use careful language such as `Procurement review requested`, `Finance/Admin review requested`, `Stock document policy review needed`, or `Supplier handoff review requested`.

Visible Warehouse copy must not use `Supplier approved`, `Supplier notified`, `Returned to supplier`, `Stock moved`, `Debit note created`, `Purchase Receipt return created`, `Purchase Invoice return created`, or `Stock Entry created` unless a later approved ERPNext process has actually completed that event.

## 5. Recommended Default

The recommended default is request-only handoff.

Warehouse should create or update a custom request/status that tells Procurement, Finance/Admin, or Admin policy owners what business decision is needed. Warehouse should not create ERPNext supplier, accounting, or stock documents.

Why this is safest:

- Warehouse stays focused on physical evidence and condition.
- Procurement keeps ownership of supplier communication, supplier authorization, claims, and PO correction.
- Finance/Admin keeps ownership of debit, payable, accounting, and document governance.
- Native ERPNext submit bypass risk stays lower.
- Warehouse users do not receive native document routes or draft document handles.
- Stock is not decreased or moved until approved document governance exists.

This default matches W15E: physical evidence first, request-only handoff second, ERPNext document policy later.

## 6. Possible Future Handoff Records

Design only. Do not implement in W15F5.

Recommended future parent record:

- `Warehouse Supplier Return Handoff Request`.

Possible parent fields:

- `supplier_return_candidate`.
- `supplier_reference_text`.
- `purchase_order_reference_text`.
- `purchase_receipt_reference_text`.
- `purchase_invoice_reference_text`.
- `warehouse_source_reference`.
- `warehouse`.
- `handoff_status`.
- `handoff_type`.
- `manager_decision`.
- `procurement_escalation_reference`.
- `finance_escalation_reference`.
- `supplier_claim_reference`.
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

- `Warehouse Supplier Return Handoff Request Line`.

Possible line fields:

- `candidate_line_reference` as plain text only.
- `item_code`.
- `item_name`.
- `warehouse`.
- `candidate_qty`.
- `supplier_return_candidate_qty`.
- `damaged_qty`.
- `wrong_item_qty`.
- `quarantine_qty`.
- `rejected_qty`.
- `condition_grade`.
- `reason_code`.
- `evidence_reference` as inert text only.
- `uom`.

Possible event record:

- `Warehouse Supplier Return Handoff Request Event`.

Possible event fields:

- `event_type`.
- `event_label`.
- `event_by`.
- `event_at`.
- `request_id`.
- `details_json`.

These records must not include native route, Link, Dynamic Link, Attach, Attach Image, HTML, Button, valuation, accounting, payable, debit, credit, rate, amount, tax, margin, profit, cost, landed cost, payment, billing, GL, email, portal, supplier notification, or customer notification fields unless a later security review explicitly approves that specific field.

## 7. Handoff Types

Future handoff types should be explicit and business-owned.

Recommended handoff types:

- `supplier_authorization_review`: Procurement must validate supplier authorization. Request only; no supplier is notified.
- `supplier_claim_review`: Procurement must review claim or dispute evidence. Request only; no claim is sent.
- `po_correction_review`: Procurement/Admin must review Purchase Order correction need. Request only; no PO is updated.
- `replacement_or_credit_review`: Procurement must review replacement or supplier-credit negotiation. Request only; no credit is approved.
- `finance_debit_review`: Finance/Admin must review debit or payable policy. Request only; no debit note or payable adjustment is created.
- `stock_document_policy_review`: Admin/Stock governance must review future stock document policy. Request only; no stock moves or posts.
- `quality_quarantine_review`: Quality/Admin must review quarantine or quality posture. Request only; no stock movement occurs.
- `supplier_handoff_review`: Procurement/Admin must review supplier pickup, shipping, or handoff readiness. Request only; no supplier is notified and no shipment is created.

Raw handoff keys must not be shown to owner-facing UI. Future UI should render business labels such as `Supplier authorization review`, `Finance/Admin debit review`, and `Stock document policy review`, each with `request only` context.

Warehouse should not use generic `approve supplier return` language because approval could be confused with supplier acceptance, stock decrease, debit approval, or ERPNext return document creation.

## 8. Eligibility Rules For Future Handoff Request

Any future handoff request method must require all of these conditions:

- A custom `Warehouse Supplier Return Candidate` exists.
- The candidate is visible to the current Warehouse context.
- The candidate has line evidence.
- The candidate has a manager-reviewed state.
- The manager state is one of the approved handoff source states.
- Supplier reference text is present.
- Warehouse source reference is present.
- Warehouse is present and visible.
- Lines have item identity.
- Candidate quantity is positive.
- Condition, reason, or evidence is present for exception posture.
- Handoff type is allowlisted.
- Handoff note is required.
- Request idempotency is enforced.
- Audit event is appended.
- Returned payload keeps all stock, supplier, accounting, document, and commercial side-effect flags false.

The future method must reject client-supplied trusted ERPNext document fields. Return Purchase Receipt, Purchase Invoice return, debit note, Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Purchase Order, supplier notification, accounting, payable, commercial, and valuation fields must not be accepted from Warehouse payload.

## 9. Allowed Source States

Potential allowed source states for a handoff request:

- `Supplier Return Candidate`.
- `Procurement Escalation`.
- `Finance/Admin Escalation`.
- `Quarantine Review`.
- `Rejected Candidate`.

State meaning:

- `Supplier Return Candidate`: Warehouse evidence suggests goods may be returned to supplier. Stock is not decreased and supplier is not notified.
- `Procurement Escalation`: Warehouse requests Procurement review. No supplier communication is sent from Warehouse.
- `Finance/Admin Escalation`: Warehouse requests Finance/Admin review. No debit note, payable adjustment, or accounting mutation occurs.
- `Quarantine Review`: Warehouse evidence indicates hold or quality review. Stock is not moved.
- `Rejected Candidate`: Warehouse manager rejected the supplier-return candidate. A handoff may be used only for closure or policy review if later approved.

`Candidate Draft`, `Physical Evidence Captured`, `Submitted For Manager Review`, and `Reinspection Requested` should normally be excluded from handoff creation because they are not final enough for downstream business review.

## 10. Role Ownership

Warehouse-owned:

- Physical evidence.
- Item identity.
- Count and condition.
- Warehouse source reference.
- Quarantine posture as custom status only.
- Manager recommendation.

Warehouse Manager / Stock Manager-owned:

- Request reinspection.
- Mark quarantine review.
- Mark supplier-return candidate.
- Escalate to Procurement.
- Escalate to Finance/Admin.
- Reject candidate.
- Request handoff only under policy.

Procurement-owned:

- Supplier communication.
- Supplier authorization.
- Supplier claims and disputes.
- Replacement or supplier credit negotiation.
- Purchase Order correction.
- Supplier handoff or pickup instruction.

Finance/Admin-owned:

- Debit note policy.
- Payable adjustment.
- Purchase Invoice return policy.
- Write-off or accounting treatment.
- ERPNext document governance.
- Native-submit containment and audit policy.

Warehouse User and Stock User must not request Procurement/Admin handoff unless a later owner-approved role policy explicitly allows it.

## 11. Blocked Boundaries

W15F5 keeps these blocked:

- Runtime code.
- Backend methods.
- DocTypes.
- UI controls.
- Smoke tests.
- Live alignment.
- Supplier notification.
- Supplier email.
- Supplier portal access.
- Procurement runtime changes.
- Sales runtime changes.
- Return Purchase Receipt creation.
- Return Purchase Receipt submission.
- Purchase Invoice return creation.
- Debit note creation.
- Stock Entry creation.
- Stock Entry submission.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Reconciliation.
- Stock decrease.
- Stock posting.
- Purchase Order update.
- Native ERPNext route exposure.
- Native `/app` route exposure.
- Native `/desk/Form` route exposure.
- Native `/desk/List` route exposure.
- Native `/desk/Report` route exposure.
- Native `/desk/query-report` route exposure.
- Valuation, accounting, payable, debit, credit, rate, amount, tax, margin, profit, cost, landed cost, payment, billing, GL, or commercial exposure.

## 12. Owner Decisions Before Runtime

Before any W15F6+ runtime implementation, owner decisions required:

- Which W15F4 states can create each handoff type?
- Can Warehouse Manager request every handoff type, or should some be Procurement/Admin-only?
- Is Procurement confirmation required before supplier handoff review can be requested?
- Can supplier return handoff exist without Purchase Order or Purchase Receipt reference text?
- Who owns close/cancel of a supplier-return handoff request?
- Can any reference become a native link later?
- Can evidence attachment/photo support be introduced later?
- Can supplier notification ever be triggered from Warehouse Console?
- Can stock document policy review ever lead to stock decrease from Warehouse Console?
- Can Finance/Admin review ever lead to debit note or payable adjustment from Warehouse Console?
- How will native-submit bypass be contained if a future ERPNext document is created?

Default recommendation:

- Keep references as plain text/status only.
- Keep attachments deferred.
- Keep supplier notification Procurement-owned and outside Warehouse runtime.
- Keep stock/accounting document creation outside Warehouse until separate owner/security approval.
- Keep handoff as request-only custom records if runtime is later approved.

## 13. Future Implementation Sequence

Recommended next phases:

1. W15F6: custom Supplier Return Handoff Request DocTypes, metadata only.
2. W15F7: request-only Procurement/Admin handoff backend, custom record only.
3. W15F8: optional UI exposure for handoff requests, inert until backend policy is accepted.
4. Later: Procurement/Admin queue integration, if owner-approved.
5. Later: ERPNext supplier return document policy, if owner-approved.

Each runtime phase should follow Safe Batch Governance:

- implement a small bounded change;
- run source validation;
- hardening review;
- security/stability review;
- operational review;
- commit and push only after acceptance.

## 14. Future Runtime Test Requirements

Any future runtime implementation must test:

- Warehouse User and Stock User denial for handoff creation.
- Manager role allowlist.
- Handoff type allowlist.
- Source-state to handoff-type mapping.
- Required handoff note.
- Required supplier/source/warehouse/line context.
- Lines derived from the source candidate, not arbitrary client rows.
- Idempotent retry.
- Changed payload rejection for reused request id.
- Cross-candidate request id reuse rejection.
- No return Purchase Receipt effect.
- No Purchase Invoice return or debit note effect.
- No Stock Entry effect.
- No Stock Ledger or Stock Balance effect.
- No Stock Reconciliation effect.
- No supplier notification.
- No Purchase Order update.
- No native ERPNext route exposure.
- No valuation/accounting/commercial payload exposure.

## 15. Acceptance Criteria For W15F5

W15F5 is acceptable when:

- Supplier return Procurement/Admin handoff policy is documented.
- Warehouse, Procurement, and Finance/Admin ownership boundaries are clear.
- Handoff is request/status only.
- ERPNext stock and accounting mutation remains blocked.
- Supplier notification remains blocked.
- Native route exposure remains blocked.
- Valuation/accounting/commercial exposure remains blocked.
- Open owner decisions are captured.
- Future implementation sequence is explicit.
- README references the W15F5 policy artifact.

## 16. Final Decision

W15F5 is a docs-only supplier return Procurement/Admin handoff policy gate.

It is safe to review as policy only. It is not approval to implement handoff runtime, supplier notification, Procurement runtime changes, Finance/Admin runtime changes, ERPNext document creation, ERPNext document submission, stock movement, native route exposure, or valuation/accounting/commercial payloads.
