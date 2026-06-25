# Warehouse Console Phase W15H1 Cycle Count / Inventory Variance Workflow Design

Date: 2026-06-25

Status: docs-only workflow design. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, pushes, Stock Reconciliation behavior, Stock Entry behavior, stock mutation, native ERPNext route exposure, valuation/accounting/commercial exposure, Sales runtime changes, Procurement runtime changes, notification behavior, email, portal access, or external actions.

Related baseline:

- W15A Warehouse operations blueprint.
- W15H Operations Closure and Next Scope Decision.
- W15C through W15G custom-record-first Warehouse workflow tracks.
- W15G10 internal transfer closure.

Reference patterns considered:

- ERPNext uses Stock Reconciliation for inventory count adjustment governance.
- Odoo inventory adjustment workflows separate counted quantity, difference, reason/reference, and apply/update actions.
- Microsoft Dynamics 365 cycle counting models count work, spot counting, location/item count planning, mobile counting, and pending-review difference resolution.

These references inform W15H1 design only. They do not approve ERPNext Stock Reconciliation, Stock Entry, stock posting, native route, or valuation/accounting exposure in Warehouse Console.

## 1. Title And Scope

W15H1 defines a controlled Warehouse cycle count and inventory variance workflow design.

The design goal is to let Warehouse capture physical count evidence and manager variance posture before any Inventory/Admin stock-adjustment decision. It follows the established W15 pattern:

- evidence first;
- manager posture second;
- request-only downstream handoff third;
- ERPNext document policy later.

W15H1 is only a design package. It does not approve runtime implementation.

W15H1 must not:

- Create Stock Reconciliation.
- Save Stock Reconciliation.
- Submit Stock Reconciliation.
- Cancel Stock Reconciliation.
- Amend Stock Reconciliation.
- Create Stock Entry.
- Save Stock Entry.
- Submit Stock Entry.
- Cancel Stock Entry.
- Amend Stock Entry.
- Create Stock Reservation.
- Reserve stock.
- Unreserve stock.
- Mutate Stock Ledger.
- Mutate Stock Balance.
- Move stock.
- Post stock.
- Update Bin.
- Update Item.
- Update Warehouse.
- Trigger customer notification.
- Trigger supplier notification.
- Send email.
- Open portal access.
- Expose native ERPNext routes.
- Expose `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report` native route patterns.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.
- Expose valuation, accounting, billing, payment, tax, landed cost, margin, profit, rate, amount, price, cost, debit, credit, payable, GL, or commercial fields.

## 2. Business Problem

Warehouse currently has controlled foundations for receiving, picking, returns, supplier returns, and internal transfers. The remaining operational gap is inventory accuracy work.

Warehouse users need a safe place to record:

- which stock/location/item was counted;
- counted quantity;
- expected quantity visibility policy;
- count evidence;
- variance reason;
- recount status;
- manager review posture;
- whether Inventory/Admin review is needed.

ERPNext stock adjustment remains separate because Stock Reconciliation can affect stock quantity, valuation, and accounting-related outcomes. Warehouse should not directly adjust stock or post Stock Ledger entries from this custom console.

## 3. Reference Design Principles

W15H1 uses these stable inventory-control principles:

- Count work should be planned by item, location, warehouse, or exception trigger.
- Spot counts should be possible later, but only as custom evidence, not stock mutation.
- Physical count and system adjustment are separate steps.
- Differences should become pending review, not automatic adjustment.
- Recount should be possible before variance escalation.
- Variance reason/evidence should be mandatory when counted quantity differs from expected posture.
- High-risk items such as serial, batch, quarantine, damaged, or restricted stock need explicit policy.
- Stock adjustment should remain Inventory/Admin-owned.

## 4. Proposed Workflow

Recommended flow:

1. Count task is planned or opened as a custom Warehouse count task.
2. Warehouse user records physical count evidence.
3. Warehouse user submits the count task for manager review.
4. Warehouse Manager or Stock Manager decides whether count is clean, requires recount, has variance, or needs Inventory/Admin review.
5. Inventory/Admin handoff is created only as custom request/status record in a later phase.
6. Stock Reconciliation policy is documented separately before any ERPNext document runtime is considered.

Normal path:

- `Planned`
- `Count In Progress`
- `Submitted For Review`
- `Clean Count`
- `Closed`

Variance path:

- `Planned`
- `Count In Progress`
- `Submitted For Review`
- `Variance Review`
- `Inventory/Admin Review Requested`

Recount path:

- `Submitted For Review`
- `Recount Requested`
- `Count In Progress`
- `Submitted For Review`

Exception path:

- `Submitted For Review`
- `Quarantine Review`, `Serial/Batch Review`, `Blocked Review`, or `Inventory/Admin Review Requested`

## 5. Proposed Future Records

Design only. Do not implement in W15H1.

Recommended first custom records:

- `Warehouse Cycle Count Task`.
- `Warehouse Cycle Count Task Line`.
- `Warehouse Cycle Count Task Event`.

Recommended later handoff records:

- `Warehouse Inventory Variance Handoff Request`.
- `Warehouse Inventory Variance Handoff Request Line`.
- `Warehouse Inventory Variance Handoff Request Event`.

All records should be app-owned custom `ERP Workspace UI` records. They should be non-submittable and should not be web-indexed.

Future records must not include native route, Link, Dynamic Link, Attach, Attach Image, HTML, Button, Currency, valuation, accounting, rate, amount, tax, cost, GL, Stock Ledger link, Stock Balance link, Stock Reconciliation link, Stock Entry link, email, portal, notification, or external-action fields unless later security review explicitly approves them.

## 6. Cycle Count Task Fields

Possible parent fields:

- `count_source`.
- `count_scope`.
- `warehouse`.
- `location_reference_text`.
- `count_status`.
- `manager_review_status`.
- `variance_status`.
- `expected_quantity_visibility`.
- `count_reason`.
- `count_priority`.
- `assigned_user`.
- `evidence_status`.
- `notes`.
- `manager_note`.
- `inventory_admin_escalation_reference`.
- `source_payload_hash`.
- `policy_version`.
- `line_count`.
- `total_counted_qty`.
- `total_variance_qty`.
- `request_id`.
- `created_by`.
- `created_at`.
- Child table `lines`.
- Child table `events`.

Possible line fields:

- `item_code`.
- `item_name`.
- `warehouse`.
- `location_reference_text`.
- `uom`.
- `expected_qty_snapshot` if visibility policy allows it.
- `counted_qty`.
- `variance_qty`.
- `variance_direction`.
- `condition_grade`.
- `reason_code`.
- `evidence_reference`.
- `serial_batch_reference_text`.
- `line_status`.

Possible event fields:

- `event_type`.
- `event_label`.
- `event_by`.
- `event_at`.
- `request_id`.
- `details_json`.

All references should be inert plain text unless later security approval allows richer behavior.

## 7. Count Source Types

Recommended count source types:

- `scheduled_cycle_count`: planned recurring count.
- `spot_count`: ad hoc count requested from Warehouse.
- `exception_count`: count triggered by shortage, overage, damage, or mismatch.
- `manager_request`: count requested by Warehouse Manager or Stock Manager.
- `inventory_admin_request`: count requested by Inventory/Admin.
- `post_movement_check`: count requested after movement visibility review.
- `return_exception_check`: count requested after customer/supplier return exception.
- `internal_transfer_check`: count requested after internal transfer candidate review.

W15H1 should not create automated count work. Runtime scheduling is a later design decision.

## 8. Count Scope

Recommended count scopes:

- Warehouse-wide sample count.
- Location/bin text reference count.
- Item-specific count.
- Item group count.
- High-risk item count.
- Serial/batch item count.
- Quarantine/restricted area count.
- Movement exception count.

Native Bin links should remain blocked by default. Location/bin should be plain text/status only until native-route containment is approved.

## 9. Expected Quantity Visibility

Owner/security must decide whether Warehouse users can see expected quantity while counting.

Recommended default:

- Use blind count for Warehouse User / Stock User.
- Manager can see variance after submission.
- Inventory/Admin can review expected-versus-counted posture during handoff.

Accepted visibility modes for future design:

- `blind_count`: Warehouse user sees item/location but not expected quantity.
- `guided_count`: Warehouse user sees expected quantity.
- `manager_visible`: expected quantity appears only during manager review.
- `inventory_admin_visible`: expected quantity appears only during Inventory/Admin review.

W15H1 recommends `blind_count` as default to reduce count bias.

## 10. Variance Classification

Variance should be classified as posture only until Inventory/Admin takes ownership.

Recommended variance states:

- `No Variance`: counted quantity matches expected posture.
- `Positive Variance`: counted quantity exceeds expected posture.
- `Negative Variance`: counted quantity is below expected posture.
- `Zero Count`: counted quantity is zero.
- `Unexpected Item`: item found where not expected.
- `Missing Item`: expected item not found.
- `Serial/Batch Review`: serial or batch evidence needs policy review.
- `Quarantine Review`: restricted, damaged, or held stock needs review.
- `Blocked Review`: count cannot be accepted due to operational blocker.

Variance state must not imply Stock Reconciliation creation or stock adjustment.

## 11. Evidence Requirements

Future count evidence should require:

- Count task id.
- Warehouse.
- Location/bin text reference when applicable.
- Item identity.
- UOM.
- Counted quantity.
- Count actor.
- Count timestamp.
- Count source.
- Count reason or trigger.
- Evidence reference as inert text when variance exists.
- Reason code when variance exists.
- Manager note for variance approval or recount request.
- Request id for idempotency.
- Source payload hash.

Exception evidence should be required for:

- Zero count.
- Unexpected item.
- Missing item.
- Positive variance.
- Negative variance.
- Damaged or quarantine posture.
- Serial/batch mismatch.
- Count blocked by access, lock, safety, or physical restriction.

## 12. Manager Decisions

Future manager decisions should be limited to internal posture.

Recommended manager decisions:

- `request_recount`: count evidence is unclear or variance needs confirmation.
- `approve_clean_count`: no variance requiring downstream review.
- `mark_variance_review`: variance exists and needs classification.
- `mark_quarantine_review`: damaged, restricted, or held stock needs quality/admin review.
- `mark_serial_batch_review`: serial or batch evidence requires Inventory/Admin policy.
- `escalate_to_inventory_admin`: request downstream stock adjustment policy review.
- `reject_count`: count task cannot be accepted.
- `close_count`: count task is closed without ERPNext stock mutation.

Manager decisions must:

- update only custom count task status/events;
- require manager role;
- require notes for non-clean decisions;
- enforce request id idempotency;
- return false stock-effect flags;
- not create Stock Reconciliation;
- not mutate stock.

## 13. Inventory/Admin Handoff

Future Inventory/Admin handoff should be request/status only.

Recommended handoff types:

- `variance_policy_review`: Inventory/Admin reviews variance policy.
- `stock_reconciliation_policy_review`: Inventory/Admin reviews whether reconciliation is allowed later.
- `serial_batch_policy_review`: Inventory/Admin reviews serial/batch count mismatch.
- `quarantine_quality_review`: Inventory/Admin or Quality reviews restricted stock posture.
- `zero_count_review`: Inventory/Admin reviews zero-count posture.
- `unexpected_item_review`: Inventory/Admin reviews item found unexpectedly.
- `close_or_cancel_review`: Inventory/Admin reviews closure ownership.

Handoff does not mean:

- Stock Reconciliation was created.
- Stock Reconciliation was submitted.
- Stock Ledger was updated.
- Stock Balance was updated.
- Stock quantity was changed.
- Valuation was changed.

## 14. Stock Reconciliation Boundary

Stock Reconciliation is blocked in W15H1.

Blocked:

- Stock Reconciliation draft creation.
- Stock Reconciliation save.
- Stock Reconciliation submit.
- Stock Reconciliation cancel.
- Stock Reconciliation amend.
- Stock Reconciliation native route exposure.
- Stock Ledger mutation.
- Stock Balance mutation.
- Valuation rate exposure.
- Difference value exposure.
- Accounting entry exposure.

If a future phase considers Stock Reconciliation draft creation, it must be a new policy gate after owner approval and Security/Stability review. It must define native-submit containment, role ownership, reference visibility, audit, idempotency, and protected gate requirements.

## 15. Native Route Boundary

W15H1 does not approve native ERPNext route exposure.

Blocked route patterns:

- `/app`
- `/desk/Form`
- `/desk/List`
- `/desk/Report`
- `/desk/query-report`

Blocked native examples:

- Stock Reconciliation form/list/report.
- Stock Entry form/list/report.
- Stock Ledger report.
- Stock Balance report.
- Stock Reservation form/list/report.
- Bin form/list/report.
- Item valuation reports.
- General Ledger report.

Future references, if shown, should remain plain text/status only unless native-route containment is separately approved.

## 16. Valuation, Accounting, And Commercial Boundary

Warehouse count and variance records, UI, payloads, and events must not expose:

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

Variance review should stay operational: item, warehouse, location/bin text, counted quantity, variance quantity, reason, evidence, recount posture, and review status.

## 17. Role Ownership

Recommended ownership:

- Warehouse User: physical count evidence.
- Stock User: physical count evidence where warehouse access allows.
- Warehouse Manager: recount and internal variance posture.
- Stock Manager: variance posture and Inventory/Admin handoff.
- Inventory/Admin: stock adjustment policy and future Stock Reconciliation governance.
- System Manager: policy override and permission governance.
- Sales: not normally involved.
- Procurement: not normally involved unless variance relates to receiving dispute or supplier return.
- Finance/Admin: involved only if adjustment has accounting/write-off impact.

Warehouse should not own Stock Reconciliation submission or accounting treatment.

## 18. Open Owner Decisions Before Runtime

Before W15H runtime implementation, owner/security must decide:

- Whether counts are scheduled, ad hoc, or both.
- Whether count is blind by default.
- Whether expected quantity can be visible to Warehouse users.
- Which warehouses are in scope.
- Whether location/bin text is enough or native Bin links are ever allowed.
- Whether serial/batch items are in scope.
- Whether count photos or attachments are allowed.
- Whether zero-count lines require manager note.
- Which variance tolerance requires manager review.
- Whether tolerance differs by item group, value band, or risk category.
- Who can request recount.
- Who can close a count task.
- Whether Inventory/Admin approval is required for every variance.
- Whether Stock Reconciliation can ever be prepared from Warehouse Console.
- Whether Warehouse can see Stock Reconciliation reference text.
- Whether native Stock Reconciliation links are blocked permanently.
- Which protected gates are mandatory before live alignment.

## 19. Future Implementation Test Requirements

Any future runtime phase must include tests proving:

- Warehouse User and Stock User can save only allowed count evidence.
- Manager decisions require Warehouse Manager, Stock Manager, or System Manager.
- Count task lines reject arbitrary stock document fields.
- Expected quantity visibility follows policy.
- Blind count mode does not leak expected quantity to Warehouse users.
- Non-negative quantities are enforced.
- Variance quantities are calculated or validated safely.
- Variance requires reason/evidence.
- Recount requires manager note.
- Idempotency returns existing result for same request and payload.
- Changed payload with same request rejects.
- Cross-task request id reuse rejects.
- No Stock Reconciliation is created.
- No Stock Reconciliation is submitted.
- No Stock Entry is created.
- No Stock Ledger mutation occurs.
- No Stock Balance mutation occurs.
- No Stock Reservation mutation occurs.
- No stock movement or posting occurs.
- No native route is exposed.
- No valuation/accounting/commercial fields are exposed.
- No Sales or Procurement runtime behavior changes.
- No notification, email, portal, or external action occurs.

## 20. Recommended Next Phase

Recommended next phase after W15H1 acceptance:

- W15H2 UI-only Cycle Count / Inventory Variance shell on Warehouse Overview.

W15H2 should remain inert and planned-only:

- no buttons that execute count save;
- no backend call;
- no native route;
- no Stock Reconciliation behavior;
- no valuation/accounting/commercial exposure.

If owner prefers to delay UI density changes, W15H2 can be skipped and W15H3 metadata can be designed after additional owner confirmation.

## 21. Acceptance Criteria For W15H1

W15H1 is acceptable when:

- It remains docs-only.
- It defines cycle count and inventory variance workflow.
- It references cross-ERP cycle count concepts without approving ERPNext mutation.
- It defines future custom records.
- It defines count source, scope, evidence, manager decisions, and handoff types.
- It blocks Stock Reconciliation.
- It blocks Stock Entry.
- It blocks stock ledger/balance/reservation mutation.
- It blocks native ERPNext routes.
- It blocks valuation/accounting/commercial exposure.
- It blocks Sales/Procurement runtime changes.
- It blocks notification/email/portal/external actions.
- It records owner decisions before runtime.
- It updates README roadmap/status only.

## 22. Final Boundary Statement

W15H1 is a docs-only workflow design for cycle count and inventory variance.

It does not implement count tasks. It does not implement manager decisions. It does not implement variance handoff. It does not create Stock Reconciliation. It does not create Stock Entry. It does not mutate Stock Ledger, Stock Balance, Stock Reservation, or stock quantity. It does not expose native ERPNext routes. It does not expose valuation/accounting/commercial fields. It does not change Sales or Procurement runtime behavior. It does not send notifications, email, portal access, or external actions.
