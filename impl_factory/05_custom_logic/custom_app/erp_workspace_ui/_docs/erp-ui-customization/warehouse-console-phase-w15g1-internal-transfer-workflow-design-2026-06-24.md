# Warehouse Console Phase W15G1 Internal Transfer Workflow Design

Date: 2026-06-24

Status: docs-only Warehouse policy and design artifact. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W8C Transfer Visibility read-only route.
- W15C inbound receiving task and manager decision foundations.
- W15D outbound picking and dispatch handoff foundations.
- W15E/W15F return intake/candidate and handoff foundations.
- Current protected Warehouse routes remain custom Warehouse routes only.

## 1. Title And Scope

W15G1 defines a future Internal Transfer Workflow policy for Warehouse Console.

Internal transfer means controlled movement of stock between warehouses, staging areas, quarantine locations, or operational holding locations inside the company. It is not a supplier return, customer return, receiving, picking, dispatch, or stock reconciliation workflow.

This is policy and design only. It does not approve runtime implementation. It does not approve ERPNext Stock Entry creation. It does not approve ERPNext Stock Entry submission. It does not approve stock movement or Stock Ledger mutation.

W15G1 must not:

- Create Stock Entry.
- Save Stock Entry.
- Submit Stock Entry.
- Cancel Stock Entry.
- Amend Stock Entry.
- Create Stock Reconciliation.
- Mutate Stock Ledger.
- Mutate Stock Balance.
- Move stock between warehouses.
- Reserve stock.
- Unreserve stock.
- Trigger picking, packing, shipping, dispatch, receiving, or supplier/customer communication.
- Update Purchase Order, Sales Order, Delivery Note, Purchase Receipt, or Purchase Invoice.
- Expose native ERPNext routes.
- Expose `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report` native route patterns.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.
- Expose valuation, accounting, billing, payment, tax, landed cost, margin, profit, rate, amount, price, cost, debit, credit, payable, GL, or commercial fields.

The purpose is to define how Warehouse should capture transfer intent, physical preparation, manager review, source/destination ownership, and future document governance before any runtime phase is considered.

## 2. Current Warehouse Context

Warehouse Console already has read-only movement and transfer visibility:

- Movement Visibility shows submitted movement posture.
- Movement Review explains posted movement evidence.
- Transfer Visibility shows read-only warehouse-to-warehouse transfer posture from submitted material-transfer Stock Entry records.

Those routes are evidence and visibility routes. They are not transfer execution routes.

Warehouse Console now also has controlled custom-record foundations for receiving, picking, dispatch handoff, customer returns, and supplier returns. W15G should follow the same pattern: physical evidence and request posture first, ERPNext document mutation later only after owner/security approval.

## 3. Business Flow In Plain English

A safe internal transfer should flow through intent, validation, physical preparation, manager approval, and later document governance.

A practical daily flow should be:

1. Warehouse identifies a need to move stock from one internal location to another.
2. The source may be replenishment, staging, quarantine release, branch transfer, operational balancing, dispatch staging, receiving putaway, or manager instruction.
3. Warehouse records item, quantity, source warehouse, target warehouse, reason, priority, and evidence/reference.
4. Warehouse user prepares or counts the transfer candidate but does not move stock in ERPNext.
5. Warehouse Manager reviews source availability, destination need, exception posture, and operational reason.
6. Manager may request recount, reject, approve as transfer candidate, mark quarantine review, or request Inventory/Admin document governance.
7. If later approved, a separate policy may allow a controlled Stock Entry draft/request owned by the proper role.
8. ERPNext remains the system of record for any eventual submitted stock movement.

Warehouse should guide controlled transfer intent and evidence. It should not silently move stock or expose native Stock Entry execution.

## 4. Entry Sources

Possible future entry sources:

- Transfer Visibility review.
- Movement Review follow-up.
- Stock Posture Review location imbalance.
- Stock Exception Review shortage/posture issue.
- Receiving putaway need after accepted receiving workflow.
- Picking shortage or staging need from outbound workflow.
- Quarantine release request.
- Branch or warehouse replenishment request.
- Manager/Admin transfer instruction.
- Cycle count or variance review recommendation, after W15H policy.

W15G1 does not approve native Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Pick List, Delivery Note, Purchase Receipt, Sales Order, Purchase Order, or query-report route links. References should remain plain text/status only until native route containment and role policy are approved.

## 5. Warehouse-Owned Steps

Warehouse owns the physical and operational side:

- Identify transfer need.
- Confirm source warehouse and target warehouse.
- Confirm item identity and UOM.
- Count requested quantity.
- Record source evidence and destination reason.
- Record exception posture such as shortage, damage, quarantine, or blocked target.
- Prepare internal transfer candidate request.
- Manager review of physical readiness and operational need.
- Later pick/pack/stage goods for transfer only if a separate policy approves that work.

Warehouse does not own automatic ERPNext stock movement, valuation, accounting, native Stock Entry lifecycle, or cross-workspace document governance.

## 6. Inventory/Admin-Owned Steps

Inventory/Admin or System/Admin owns stock document governance:

- Whether a Stock Entry draft/request may be prepared.
- Whether source and target warehouses are allowed.
- Whether target warehouse can receive the item.
- Whether quarantine/restricted stock can be transferred.
- Whether stock reservation is needed.
- Whether transfer should be blocked due to open demand, batch/serial policy, or compliance.
- Whether a submitted Stock Entry is eventually allowed.
- Native-submit containment and audit policy.

Warehouse Manager may request transfer governance, but ERPNext stock document creation/submission remains a later owner-approved phase.

## 7. Recommended W15G Default

Recommended safest default:

- Warehouse creates only custom Internal Transfer Candidate records.
- Warehouse Manager may request Inventory/Admin review.
- No Stock Entry is created.
- No Stock Entry is submitted.
- No Stock Ledger entry is created.
- No Stock Balance mutation is performed.
- No stock reservation is created.
- No native route is exposed.
- No valuation/accounting/commercial fields are exposed.

This mirrors W15C/W15D/W15E/W15F: evidence first, manager posture second, request-only handoff third, ERPNext document policy later.

## 8. Proposed Future Custom Records

Design only. Do not implement in W15G1.

Potential parent record:

- `Warehouse Internal Transfer Candidate`.

Possible parent fields:

- `source_context`.
- `source_reference_text`.
- `source_warehouse`.
- `target_warehouse`.
- `transfer_reason`.
- `transfer_priority`.
- `candidate_status`.
- `manager_review_status`.
- `inventory_admin_escalation_reference`.
- `quarantine_review_reference`.
- `source_payload_hash`.
- `policy_version`.
- `request_id`.
- `created_by`.
- `created_at`.
- Child table `lines`.
- Child table `events`.

Potential child line record:

- `Warehouse Internal Transfer Candidate Line`.

Possible line fields:

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
- `evidence_reference`.
- `uom`.

Potential event record:

- `Warehouse Internal Transfer Candidate Event`.

Possible event fields:

- `event_type`.
- `event_label`.
- `event_by`.
- `event_at`.
- `request_id`.
- `details_json`.

These records must not include valuation, accounting, payable, debit, credit, rate, amount, tax, margin, profit, cost, landed cost, payment, billing, GL, native route, Link, Dynamic Link, Attach, HTML, Button, email, portal, reservation, Stock Entry lifecycle, Stock Ledger, Stock Balance, or Stock Reconciliation fields unless later security review explicitly approves a different design.

## 9. Status Model

Suggested internal status model:

- `Draft`.
- `Count In Progress`.
- `Submitted For Review`.
- `Recount Requested`.
- `Transfer Candidate`.
- `Quarantine Review`.
- `Inventory/Admin Review`.
- `Rejected`.
- `Cancelled`.
- `Closed`.

Status meanings:

- `Draft`: physical transfer intent captured, not manager-reviewed.
- `Count In Progress`: Warehouse is checking physical quantity/readiness.
- `Submitted For Review`: ready for manager review.
- `Recount Requested`: manager needs another count or evidence check.
- `Transfer Candidate`: manager recommends transfer, but no stock movement is created.
- `Quarantine Review`: item/location requires quality or restricted-stock review.
- `Inventory/Admin Review`: request-only handoff for stock document policy.
- `Rejected`: manager rejects transfer candidate.
- `Cancelled`: owner cancels the custom candidate record.
- `Closed`: custom workflow is closed without implying ERPNext stock posting.

No status may imply stock has moved, Stock Entry has been created, Stock Entry has been submitted, or Stock Ledger has changed.

## 10. Warehouse User Preview

Future UI may show planned controls such as:

- `Start transfer check`.
- `Count source quantity`.
- `Record target warehouse`.
- `Add evidence reference`.
- `Save transfer draft`.
- `Send to manager review`.

Until a runtime phase is approved, these controls must be inert planned shell elements only. If later implemented, they must write only custom internal transfer records and return false stock-effect flags.

## 11. Manager Decision Preview

Future manager decisions may include:

- `request_recount`.
- `approve_transfer_candidate`.
- `mark_quarantine_review`.
- `escalate_to_inventory_admin`.
- `reject_transfer_candidate`.
- `cancel_transfer_candidate`.
- `close_transfer_candidate`.

Decision wording must remain request/recommendation wording. Avoid labels like `Approve transfer`, `Move stock`, `Create Stock Entry`, or `Post transfer` unless a later approved phase explicitly adds a controlled document path.

## 12. Transfer Evidence Requirements

Minimum evidence for a future backend phase:

- Source warehouse.
- Target warehouse.
- Item code and item name.
- Requested quantity.
- Counted or candidate quantity.
- UOM.
- Transfer reason.
- Source context or manager note.
- Evidence reference or note for exception/blocked/quarantine quantities.
- Request id for idempotency.
- Policy version.

Additional evidence may be required later for:

- Batch/serial items.
- Quarantine transfers.
- High-value items.
- Cross-branch transfers.
- Regulated stock.
- Transfer into dispatch staging.
- Transfer out of receiving or quarantine.

## 13. Exception Policy

Default exception handling:

- Short quantity blocks clean transfer candidate approval unless manager records a reason.
- Damaged quantity cannot be normal-transfer candidate quantity.
- Quarantine quantity requires quality/quarantine review.
- Wrong source warehouse blocks transfer candidate creation.
- Unsupported target warehouse blocks transfer candidate creation.
- Invisible source or target warehouse blocks transfer candidate creation.
- Negative quantities are rejected.
- Candidate quantity cannot exceed counted quantity.
- Candidate quantity cannot exceed visible source posture, if source posture is available.
- Batch/serial items are deferred until a separate policy approves exact handling.

W15G1 does not approve substitution, auto-replenishment, route optimization, reservation, or transfer execution.

## 14. Future Stock Entry Policy Boundary

Stock Entry draft/request policy is a later phase only.

Before any Stock Entry draft/request implementation, owner and Security/Stability must decide:

- Whether Warehouse Manager can request a Stock Entry draft or only Inventory/Admin can create it.
- Whether Stock Entry draft creation happens in Warehouse Console at all.
- Whether draft references can be visible to Warehouse users.
- Whether draft references are plain text/status only or native links.
- Whether native-submit bypass containment is sufficient.
- Whether transfer target/source warehouses are restricted by policy.
- Whether serial/batch items are in scope.
- Whether stock reservation is ever allowed.
- Whether submitted Stock Entry remains exclusively outside Warehouse Console.

Default recommendation: Warehouse may request Inventory/Admin review only. Do not create Stock Entry draft from Warehouse Console until the custom workflow is proven and native-submit containment is approved.

## 15. Role Ownership

Recommended role ownership:

- Warehouse User: capture physical transfer intent/count evidence only.
- Stock User: capture physical transfer intent/count evidence only where warehouse access allows.
- Warehouse Manager: review and recommend internal transfer posture.
- Stock Manager: review transfer posture and inventory policy.
- System Manager: policy/admin override.
- Inventory/Admin: ERPNext stock document governance.
- Sales: not involved unless transfer affects customer dispatch promise.
- Procurement: not involved unless transfer is tied to supplier return or receiving dispute.
- Finance/Admin: not involved unless later accounting/write-off policy applies.

Warehouse Console must not grant normal Warehouse users stock document lifecycle authority.

## 16. UI Structure Recommendation

Future W15G2 UI shell should appear in Warehouse Overview or Transfer Visibility as a planned lane named:

- `Internal transfer candidate`.

Recommended sections:

- `Transfer Source`.
- `Target Warehouse`.
- `Physical Count`.
- `Manager Review`.
- `Inventory/Admin Review`.
- `Document Policy`.

Recommended guardrail copy:

- `No stock is moved, no Stock Entry is created or submitted, and no Stock Ledger or Stock Balance record is changed from this shell.`

Do not show raw enum keys in owner-facing UI. Render business labels such as `Inventory/Admin review requested` and `Transfer candidate only, no stock moved`.

## 17. Hardening Requirements For Future Runtime

Any future runtime phase must include:

- Server-side role gate.
- Warehouse access validation for source and target warehouses.
- Source line ownership validation.
- No client-trusted warehouse, item, or quantity authority.
- Bounded plain-text references only.
- Non-negative quantity validation.
- Candidate quantity limits.
- Duplicate line rejection.
- Required evidence for exception quantities.
- Request-id idempotency.
- Changed-payload rejection.
- Cross-record request-id reuse rejection.
- Safe payload flags with stock effect false.
- Hidden valuation object.
- No native route links.
- Tests proving no Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Stock Reservation, or stock posting path.

## 18. Test Plan For Future Phases

Future source tests should verify:

- Custom records are non-submittable.
- Warehouse User/Stock User permissions are bounded to the approved phase.
- Manager decisions require manager roles.
- Wrong source warehouse rejects.
- Wrong target warehouse rejects.
- Invisible warehouse rejects.
- Duplicate lines reject.
- Negative quantities reject.
- Candidate quantity over counted quantity rejects.
- Exception quantities require note/evidence.
- Idempotency returns existing safe payload.
- Changed payload with same request rejects.
- Cross-record request reuse rejects.
- No `frappe.set_route` to native routes.
- No `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report` exposure.
- No Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Stock Reservation, or submitted stock mutation path.
- No valuation/accounting/commercial fields in UI, payload, DocTypes, or events.

## 19. Recommended Phase Sequence

Recommended W15G sequence:

- W15G1: docs-only internal transfer workflow design.
- W15G2: UI shell only, planned controls inert, no backend write.
- W15G3: custom Internal Transfer Candidate metadata only.
- W15G4: save transfer candidate draft backend, custom records only.
- W15G5: manager decision backend, custom status/event only.
- W15G6: Inventory/Admin handoff policy docs.
- W15G7: custom handoff request metadata only.
- W15G8: request-only Inventory/Admin handoff backend.
- W15G9: optional Stock Entry draft policy docs, if owner approves.
- W15G10: protected gates and owner manual review.

No phase should create or submit Stock Entry unless a later explicit owner/security-approved policy authorizes that exact behavior.

## 20. Open Owner Decisions

Before runtime implementation, decide:

- Can Warehouse create internal transfer candidates directly, or only from existing Transfer Visibility/Stock Posture contexts?
- Which users can create transfer candidate drafts?
- Which managers can approve transfer candidate posture?
- Which warehouses are valid transfer sources and targets?
- Are quarantine transfers allowed?
- Are serial/batch items included or deferred?
- Is stock reservation ever allowed?
- Can a Stock Entry draft ever be created from Warehouse Console?
- If a Stock Entry draft is created later, who owns it?
- Can Warehouse users see a draft reference, and if so is it plain text only?
- Who closes/cancels internal transfer candidates?
- What evidence is mandatory for transfer request, exception, and quarantine paths?
- What native-submit bypass containment is required before any Stock Entry draft phase?

Default recommendation: start with custom transfer candidate records only, no Stock Entry draft, no reservation, no native links, no stock movement.

## 21. Acceptance Criteria For W15G1

W15G1 is acceptable when:

- It remains docs-only.
- It clearly separates Warehouse physical transfer evidence from ERPNext stock movement.
- Stock Entry creation/submission remains blocked.
- Stock Ledger and Stock Balance mutation remain blocked.
- Stock Reconciliation and Stock Reservation remain blocked.
- Native ERPNext route exposure remains blocked.
- Valuation/accounting/commercial exposure remains blocked.
- Sales and Procurement runtime changes remain blocked.
- Open owner decisions are explicit before implementation.

## 22. Boundary Confirmation

This document changes no runtime behavior. It creates no backend method, DocType, UI shell, smoke, live file, stock document, native route, or stock movement.

W15G1 is only a policy and design artifact for future controlled Internal Transfer workflow planning.
