# Warehouse Console Phase W15F1 Supplier Return Workflow Design

Date: 2026-06-22

Status: docs-only Warehouse policy and design artifact. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W15C inbound receiving workflow and Purchase Receipt draft policy.
- W15E customer return intake, disposition, and Sales/Admin handoff policy.
- Current protected Warehouse routes remain custom Warehouse routes only.

## 1. Title And Scope

W15F1 defines a future Supplier Return Workflow policy for Warehouse Console.

Supplier return means goods that the business intends to return to a supplier because of damage, wrong item, quality issue, over-receipt dispute, rejected receiving, warranty claim, or supplier agreement.

This is policy and design only. It does not approve runtime implementation. It does not approve ERPNext supplier return document creation. It does not approve ERPNext supplier return document submission. It does not approve stock mutation.

W15F1 must not:

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

The purpose is to define how Warehouse should capture physical supplier-return evidence and request downstream Procurement/Admin governance before any runtime phase is considered.

## 2. Current Warehouse Context

Warehouse Console now has controlled receiving, picking, dispatch, and customer-return foundations.

Current state:

- W15C receiving work can save custom receiving tasks and manager decisions.
- W15C5 keeps Purchase Receipt draft creation and submission blocked until later owner approval.
- W15D dispatch work can save custom picking tasks, manager decisions, and dispatch handoff requests.
- W15E customer return work can save custom intake, manager decisions, and request-only Sales/Admin handoff records.
- Supplier returns are not implemented.
- Warehouse Console currently must not create supplier return documents, stock entries, debit notes, or supplier notifications.

Supplier returns are more sensitive than internal evidence capture because they cross Procurement ownership, supplier communication, commercial claims, payable adjustments, and stock movement.

## 3. Business Flow In Plain English

A supplier return starts from physical goods and a supplier-facing business decision.

A practical daily flow should be:

1. Warehouse finds goods that may need to go back to a supplier.
2. The source may be damaged receiving, wrong item, quarantine, over-receipt dispute, failed inspection, expired supplier warranty, or Procurement instruction.
3. Warehouse records which item, quantity, supplier context, warehouse, condition, and evidence.
4. Warehouse Manager reviews the physical evidence.
5. Warehouse Manager marks the goods as supplier-return candidate or requests reinspection/quarantine.
6. Procurement reviews whether the supplier return is valid and owns supplier communication.
7. Finance/Admin reviews whether debit note, payable adjustment, or accounting treatment is needed.
8. If later approved, an ERPNext return or movement document may be prepared by the proper owner under a separate policy.
9. Warehouse may later pick/pack/handoff goods for supplier pickup or shipment, but only after Procurement/Admin approval.
10. ERPNext remains the system of record for any eventual stock or accounting document.

Warehouse should guide physical evidence and controlled handoff, not silently move stock or create supplier-facing documents.

## 4. Entry Sources

Possible future entry sources:

- Receiving discrepancy from W15C.
- Damaged or wrong item identified during receiving.
- Quarantine review from receiving.
- Procurement-approved supplier return request.
- Supplier warranty or replacement request.
- Quality inspection failure.
- Over-receipt dispute.
- Supplier paperwork mismatch.
- Existing stock identified as supplier-defective.

W15F1 does not approve native Purchase Order, Purchase Receipt, Purchase Invoice, Stock Entry, Stock Ledger, or supplier route links. References should remain plain text/status only until native route containment and role policy are approved.

## 5. Warehouse-Owned Steps

Warehouse owns the physical side:

- Identify goods proposed for supplier return.
- Confirm item identity.
- Count quantity.
- Confirm warehouse/location.
- Record condition and evidence.
- Segregate or mark quarantine posture as custom status only.
- Prepare internal return candidate request.
- Manager review of physical return evidence.
- Pack/handoff readiness later, if approved.

Warehouse does not own supplier dispute, supplier communication, commercial claim, debit note, payable adjustment, or accounting outcome.

## 6. Procurement-Owned Steps

Procurement owns supplier and PO governance:

- Supplier communication.
- Supplier return approval.
- Supplier replacement/credit negotiation.
- Purchase Order correction.
- Supplier claim reference.
- Supplier-side paperwork requirements.
- Whether return is accepted by supplier.
- Whether replacement, credit, or dispute path is required.

Warehouse should escalate supplier-facing decisions to Procurement instead of duplicating those workflows.

## 7. Finance/Admin-Owned Steps

Finance/Admin owns accounting and document governance:

- Debit note or supplier credit policy.
- Purchase Invoice return governance.
- Payable adjustment.
- Write-off policy.
- Accounting document governance.
- ERPNext document creation and submission, if later approved.
- Native-submit containment and audit policy.

Warehouse should never decide payable, debit, GL, rate, tax, or amount outcomes.

## 8. Recommended W15F Default

Recommended safest default:

- Warehouse creates only custom Supplier Return Candidate records.
- Warehouse Manager may request Procurement/Admin review.
- No stock is decreased.
- No return Purchase Receipt is created.
- No Purchase Invoice return or debit note is created.
- No Stock Entry is created.
- No Stock Ledger entry is created.
- No supplier notification is sent.
- No native route is exposed.

This mirrors W15E: physical evidence first, request-only handoff second, ERPNext document policy later.

## 9. Proposed Future Custom Records

Design only. Do not implement in W15F1.

Potential parent record:

- `Warehouse Supplier Return Candidate`.

Possible parent fields:

- `supplier_reference_text`.
- `purchase_order_reference_text`.
- `purchase_receipt_reference_text`.
- `purchase_invoice_reference_text`.
- `source_context`.
- `warehouse`.
- `candidate_status`.
- `manager_review_status`.
- `procurement_escalation_reference`.
- `finance_escalation_reference`.
- `supplier_return_reason`.
- `evidence_reference`.
- `source_payload_hash`.
- `policy_version`.
- `request_id`.
- `created_by`.
- `created_at`.
- Child table `lines`.
- Child table `events`.

Potential child line record:

- `Warehouse Supplier Return Candidate Line`.

Possible line fields:

- `item_code`.
- `item_name`.
- `warehouse`.
- `candidate_qty`.
- `damaged_qty`.
- `wrong_item_qty`.
- `quarantine_qty`.
- `supplier_return_candidate_qty`.
- `rejected_qty`.
- `condition_grade`.
- `reason_code`.
- `evidence_reference`.
- `uom`.

Potential event record:

- `Warehouse Supplier Return Candidate Event`.

Possible event fields:

- `event_type`.
- `event_label`.
- `event_by`.
- `event_at`.
- `request_id`.
- `details_json`.

These records must not include valuation, accounting, payable, debit, credit, rate, amount, tax, margin, profit, cost, landed cost, payment, billing, GL, native route, Link, Dynamic Link, Attach, HTML, email, portal, or supplier notification fields unless later security review explicitly approves a different design.

## 10. Status Model

Future custom Supplier Return Candidate statuses:

- `Candidate Draft`.
- `Submitted For Manager Review`.
- `Reinspection Requested`.
- `Quarantine Review`.
- `Supplier Return Candidate`.
- `Procurement Review Requested`.
- `Finance/Admin Review Requested`.
- `Supplier Return Approved Externally`.
- `Return Packing Ready`.
- `Supplier Handoff Requested`.
- `Closed`.
- `Cancelled`.

Important wording:

- `Supplier Return Candidate` means evidence suggests goods may be returned to supplier.
- It does not mean stock moved.
- It does not mean supplier accepted the return.
- It does not mean debit, credit, or replacement is approved.

## 11. Manager Decisions

Future Warehouse Manager decisions may include:

- `request_reinspection`.
- `mark_quarantine_review`.
- `mark_supplier_return_candidate`.
- `escalate_to_procurement`.
- `escalate_to_finance_admin`.
- `reject_supplier_return_candidate`.
- `mark_return_packing_ready`.
- `request_supplier_handoff`.

These decisions must update only custom Warehouse status/events until a later approved runtime phase.

Manager decisions must not:

- Create return Purchase Receipt.
- Create Purchase Invoice return.
- Create debit note.
- Create Stock Entry.
- Post stock.
- Notify supplier.
- Update Purchase Order.
- Expose native ERPNext document routes.

## 12. Procurement/Admin Handoff Types

Future request-only handoff types may include:

- `supplier_authorization_review`.
- `supplier_claim_review`.
- `po_correction_review`.
- `replacement_or_credit_review`.
- `finance_debit_review`.
- `stock_document_policy_review`.
- `quality_quarantine_review`.
- `supplier_handoff_review`.

These should render as business labels in UI. Raw keys must not be shown to users.

Suggested labels:

- `supplier_authorization_review` -> `Supplier authorization review`.
- `supplier_claim_review` -> `Supplier claim review`.
- `po_correction_review` -> `Purchase order correction review`.
- `replacement_or_credit_review` -> `Replacement or supplier credit review`.
- `finance_debit_review` -> `Finance/Admin debit review`.
- `stock_document_policy_review` -> `Stock document policy review`.
- `quality_quarantine_review` -> `Quality/quarantine review`.
- `supplier_handoff_review` -> `Supplier handoff review`.

Each label should include context like `request only, no supplier notified` or `request only, no stock moved` when shown in Warehouse UI.

## 13. Evidence Requirements

Supplier return evidence should include:

- Supplier or supplier reference text.
- Source context such as receiving discrepancy, quarantine, PO/PR/PI text reference, or Procurement instruction.
- Warehouse.
- Item identity.
- Quantity.
- Condition grade or note.
- Reason code.
- Evidence reference if damaged, wrong item, quarantine, supplier dispute, or paperwork mismatch.
- Manager note for review or escalation.
- Idempotency request id.

Future attachment or photo support needs separate security review for upload permissions, storage, visibility, and external access.

## 14. Role Model

Recommended future role behavior:

- Warehouse User / Stock User: create or save physical candidate draft evidence only.
- Warehouse Manager / Stock Manager: manager review and request-only handoff.
- Procurement User / Procurement Manager: review supplier-facing handoff in Procurement-owned workflow later.
- Finance/Admin: review debit/accounting policy later.
- System Manager: configure policy and emergency correction.

W15F1 does not grant Procurement, Finance/Admin, or supplier-facing runtime behavior.

## 15. Future ERPNext Mapping

Future mapping may be considered only after owner/security approval:

- Return Purchase Receipt, if a controlled supplier return against receipt is approved.
- Purchase Invoice return or debit note, if Finance/Admin policy approves.
- Stock Entry, if approved movement/issue workflow is required.
- Stock Reconciliation only for separately governed adjustment cases.

All mappings must remain future policy until explicit implementation approval.

No future implementation should directly submit ERPNext stock or accounting documents from Warehouse Console without:

- owner approval;
- role policy;
- idempotency;
- audit log;
- native-submit bypass containment;
- protected gates;
- security review;
- operation review;
- manual owner review.

## 16. Blocked In W15F1

Blocked:

- Runtime code.
- Backend methods.
- DocTypes.
- UI controls.
- Smoke tests.
- Live alignment.
- Supplier notification.
- Procurement runtime changes.
- Sales runtime changes.
- Return Purchase Receipt creation.
- Purchase Invoice return or debit note creation.
- Stock Entry creation.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Reconciliation.
- Stock decrease/posting.
- Purchase Order update.
- Native ERPNext route exposure.
- Native /app, /desk/Form, /desk/List, /desk/Report, or /desk/query-report exposure.
- Valuation/accounting/commercial exposure.

## 17. Open Owner Decisions

Before any runtime implementation, owner decisions required:

- Can Warehouse create supplier return candidates directly, or only from receiving/quarantine source records?
- Is Procurement approval required before physical supplier-return candidate creation?
- Which source contexts are allowed: receiving damage, wrong item, quarantine, existing stock defect, warranty, overage dispute?
- Can candidates exist without Purchase Order or Purchase Receipt reference?
- Which warehouses may hold supplier-return candidates?
- Is evidence/photo mandatory for all supplier returns or only exception types?
- Who owns supplier communication?
- Who owns debit note/payable adjustment?
- Who can close or cancel supplier-return candidates?
- Can supplier handoff be requested before Procurement approval?
- Will future supplier handoff create a custom request only or an ERPNext document draft?
- Can any reference become a native link later?
- How will native-submit bypass be contained?

## 18. Recommended Implementation Sequence

Recommended next phases:

1. W15F2: UI shell only on Warehouse Overview or Action Center for Supplier Return Candidate, no active controls.
2. W15F3: custom Supplier Return Candidate DocTypes, metadata only.
3. W15F4: save Supplier Return Candidate draft backend, custom record only.
4. W15F5: Supplier Return manager decision backend, custom status/events only.
5. W15F6: Procurement/Admin handoff policy, docs-only.
6. W15F7: custom handoff request DocTypes, metadata only.
7. W15F8: request-only Procurement/Admin handoff backend.
8. Later: owner-approved ERPNext supplier return document policy, if still required.

Each runtime phase should follow Safe Batch Governance:

- implement a small bounded change;
- run source validation;
- hardening review;
- security/stability review;
- operational review;
- commit and push only after acceptance.

## 19. Acceptance Criteria For W15F1

W15F1 is acceptable when:

- Supplier return business flow is documented.
- Warehouse, Procurement, and Finance/Admin ownership boundaries are clear.
- ERPNext stock and accounting mutation remains blocked.
- Native route exposure remains blocked.
- Valuation/accounting/commercial exposure remains blocked.
- Open owner decisions are captured.
- Future implementation sequence is explicit.
- README references the W15F1 design artifact.

## 20. Final Decision

W15F1 is a docs-only supplier return workflow design gate.

It is safe to review as policy only. It is not approval to implement supplier return runtime, stock movement, supplier communication, Procurement runtime, Finance/Admin runtime, ERPNext document creation, ERPNext document submission, native route exposure, or valuation/accounting/commercial payloads.
