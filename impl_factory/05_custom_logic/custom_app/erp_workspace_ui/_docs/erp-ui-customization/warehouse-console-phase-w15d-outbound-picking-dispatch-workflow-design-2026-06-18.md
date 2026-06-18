# Warehouse Console Phase W15D Outbound Picking And Dispatch Workflow Design

Date: 2026-06-18

Status: docs-only Warehouse design artifact. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15A Warehouse operations blueprint.
- W15C inbound receiving workflow design.
- W15C5 controlled Purchase Receipt draft policy.
- Current protected outbound routes:
  - `/desk/warehouse-console-worklist/outbound-picking`.
  - `/desk/warehouse-console-picking/<sales-order>`.

## 1. Objective

W15D defines a future controlled outbound picking and dispatch workflow for Warehouse Console.

The goal is to move from read-only Outbound Picking visibility into a controlled task workflow where Warehouse can capture physical picking, packing, dispatch handoff evidence, shortage signals, damage signals, and partial fulfillment posture.

W15D does not approve direct stock mutation. It does not approve Delivery Note draft creation or Delivery Note submission. It defines the policy and workflow required before any later implementation phase can be approved.

The future workflow should support:

- Warehouse User pick task evidence.
- Picked quantity, short quantity, damaged quantity, and not-found evidence.
- Packing and dispatch handoff evidence.
- Manager review and decision.
- Clean, partial, blocked, shortage, and Sales escalation outcomes.
- Later Delivery Note draft policy, only after separate approval.

W15D must not:

- Create or submit Delivery Note.
- Create Pick List.
- Create Stock Reservation.
- Reserve or unreserve stock.
- Post stock.
- Create Stock Ledger entries.
- Expose native ERPNext routes.
- Expose valuation, accounting, payment, billing, margin, cost, amount, rate, or commercial fields.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.

## 2. Current State

Warehouse Console currently has protected custom outbound routes:

- `/desk/warehouse-console-worklist/outbound-picking`.
- `/desk/warehouse-console-picking/<sales-order>`.

The Outbound Picking queue shows sales-order demand and picking posture. The Picking Review page shows read-only Sales Order identity, customer, delivery timing, item rows, ordered quantity, delivered quantity, pending quantity, warehouse availability posture, and custom Warehouse drilldowns.

Current limitations:

- Picking posture is read-only.
- There is no Warehouse Picking Task record.
- There is no save pick draft action.
- There is no packing evidence.
- There is no dispatch handoff evidence.
- There is no manager release or approval workflow.
- There is no Delivery Note draft policy.
- There is no stock reservation.
- There is no Pick List creation.
- There is no shipping, delivery, or stock posting.
- There are no native ERPNext Sales Order, Delivery Note, Pick List, Stock Entry, Stock Ledger, or Stock Balance route links.

## 3. Design Principles

W15D must follow these principles:

- No silent stock mutation. Picking tasks capture evidence and posture; stock changes happen only through separately governed ERPNext documents.
- No Delivery Note submission. Submission remains out of scope until a later owner-approved phase.
- No native ERPNext route escape. Navigation remains in custom Warehouse routes.
- Sales owns customer and commercial decisions. Warehouse owns physical pick, pack, dispatch handoff evidence, and warehouse-side shortage visibility.
- Role-based workflow. Warehouse User, Warehouse Manager, Sales, and System/Admin responsibilities remain separate.
- Audit trail required. Every future save, review submit, manager decision, release, handoff, and draft request must be auditable.
- Idempotency required. Replayed requests must not duplicate tasks, events, releases, or future drafts.
- No valuation or commercial exposure. Do not show rates, amounts, taxes, margins, cost, GL, billing, payment, or customer commercial terms.
- No Quick Find write action. Search surfaces must not trigger outbound execution.

## 4. Roles

### Warehouse User

Warehouse User performs the physical pick and pack evidence work.

Responsibilities:

- Open Outbound Picking queue and Picking Review.
- Start a pick task when work is ready.
- Confirm sales order, customer, source warehouse, delivery timing, and item context shown by the server.
- Record picked quantity per line.
- Record shortage, damage, not-found, wrong-bin, or unavailable stock evidence.
- Record packing readiness where policy allows.
- Record dispatch handoff evidence where policy allows.
- Add notes and evidence references.
- Submit the pick task for manager review.

Forbidden:

- Approve or release the task.
- Create Pick List.
- Create Delivery Note.
- Submit Delivery Note.
- Reserve or unreserve stock.
- Post stock.
- Change Sales Order, customer commitment, commercial terms, rates, taxes, payment, or billing context.
- Open native ERPNext forms or reports from Warehouse.

### Warehouse Manager / Stock Manager

Warehouse Manager reviews picking tasks and decides the warehouse-side outcome.

Responsibilities:

- Review clean and discrepant picks.
- Request repick or recount when evidence is unclear.
- Approve clean pick evidence.
- Approve partial pick when policy allows.
- Mark shortage review.
- Resolve warehouse-side not-found or wrong-bin evidence.
- Mark pack ready.
- Mark dispatch handoff ready.
- Escalate customer-facing partial fulfillment or shortage to Sales.
- Authorize Delivery Note draft preparation only in a later policy phase.

Forbidden in W15D:

- Submit Delivery Note.
- Post stock.
- Override Sales-owned customer, partial shipment, pricing, terms, or commitment decisions.
- Use native ERPNext form or report escape from Warehouse.

### Sales User / Sales Manager

Sales remains owner of customer-facing and commercial outbound decisions.

Responsibilities:

- Own customer communication.
- Own Sales Order changes.
- Own customer commitment and promised-date changes.
- Decide partial shipment approval when customer-facing or commercial policy requires it.
- Receive shortage, not-found, damage, or partial fulfillment signals from Warehouse.

Sales users should not receive Warehouse task execution rights in W15D unless a later owner-approved policy explicitly grants them.

### System/Admin

System/Admin configures workflow policy later.

Responsibilities:

- Configure roles and warehouse scope.
- Configure shortage tolerance and partial fulfillment policy.
- Configure dispatch evidence requirements.
- Configure whether Pick List, Stock Reservation, or Delivery Note draft integration is ever allowed.
- Configure who can close or cancel outbound tasks.

## 5. Daily Flow

Recommended outbound operating flow:

1. Sales Order exists and remains open for delivery.
2. Warehouse sees open demand in Outbound Picking.
3. Warehouse User opens Picking Review for the Sales Order.
4. Warehouse User starts a pick task.
5. Warehouse User confirms source warehouse and line context.
6. Warehouse User picks and counts items.
7. Warehouse User records per line:
   - ordered quantity;
   - delivered quantity;
   - pending quantity;
   - picked quantity;
   - packed quantity;
   - short quantity;
   - damaged quantity;
   - not-found quantity;
   - accepted for dispatch quantity.
8. Warehouse User records evidence reference and notes for shortage, damage, not-found, wrong-bin, or dispatch paperwork mismatch.
9. Warehouse User submits the task for manager review.
10. Warehouse Manager reviews evidence.
11. Manager chooses one outcome:
   - approve clean pick;
   - approve partial pick;
   - request repick or recount;
   - mark shortage review;
   - escalate to Sales;
   - mark pack ready;
   - mark dispatch handoff ready.
12. Sales decides customer-facing partial shipment, customer communication, or Sales Order correction where required.
13. Delivery Note draft preparation remains a later governed policy if approved.
14. Delivery Note submission remains outside W15D.
15. No stock is posted from the W15D task shell.

## 6. Custom Route And Page Strategy

Keep the current Outbound Picking queue as the entry point:

- `/desk/warehouse-console-worklist/outbound-picking`.

Use the current Picking Review as the primary operational page:

- `/desk/warehouse-console-picking/<sales-order>`.

Future W15D2 UI shell should add an outbound task panel inside Picking Review rather than creating a separate first-step page. This keeps context close to existing read-only picking posture and avoids native Sales Order form behavior.

Add a custom task detail route later only if task evidence becomes too large for Picking Review:

- `/desk/warehouse-console-picking-task/<task-id>`.

Do not expose native routes for:

- Sales Order.
- Delivery Note.
- Pick List.
- Stock Entry.
- Stock Ledger.
- Stock Balance.
- Stock Reservation Entry.

## 7. Data Model Proposal

No implementation is approved in this document.

### Warehouse Picking Task

Purpose: parent record for one controlled outbound pick/pack/dispatch handoff task against a Sales Order.

Candidate fields:

- `task_id`
- `sales_order`
- `customer`
- `source_warehouse`
- `status`
- `assigned_user`
- `manager`
- `started_at`
- `submitted_at`
- `reviewed_at`
- `decision`
- `notes`
- `source_route`
- `policy_version`
- `last_request_id`

Rules:

- Sales Order, customer, and source warehouse must be server-derived or server-validated.
- The task must not store rates, amounts, taxes, valuation, payment, billing, margin, cost, or customer commercial fields.
- One active task per Sales Order and source warehouse should be the default unless a manager override is later approved.

### Warehouse Picking Task Line

Purpose: line-level physical picking and packing evidence.

Candidate fields:

- `sales_order_item`
- `item_code`
- `item_name`
- `uom`
- `ordered_qty`
- `delivered_qty`
- `pending_qty`
- `available_qty`
- `picked_qty`
- `packed_qty`
- `short_qty`
- `damaged_qty`
- `not_found_qty`
- `accepted_for_dispatch_qty`
- `source_warehouse`
- `discrepancy_reason`
- `note`
- `evidence_reference`
- `line_status`

Rules:

- Server recomputes pending quantity from Sales Order Item and delivered posture.
- Server validates that each line belongs to the selected Sales Order.
- Server rejects negative quantities and impossible combinations.
- `accepted_for_dispatch_qty` must not exceed policy-approved picked/packed quantity.
- Damaged, not-found, and shortage evidence must be captured before manager decisions.

### Warehouse Picking Task Event

Purpose: immutable outbound task workflow trace.

Candidate fields:

- `event_type`
- `actor`
- `timestamp`
- `task_id`
- `previous_status`
- `next_status`
- `note`
- `server_request_id`
- `policy_version`

Candidate event types:

- `started_pick_task`
- `saved_pick_draft`
- `submitted_for_review`
- `requested_repick`
- `approved_clean_pick`
- `approved_partial_pick`
- `marked_shortage_review`
- `marked_pack_ready`
- `marked_dispatch_handoff_ready`
- `escalated_to_sales`
- `delivery_draft_requested`
- `delivery_draft_prepared`
- `closed`
- `cancelled`

## 8. Status Model

Statuses are Warehouse task statuses, not ERPNext Delivery Note or stock document statuses.

| Status | Who Can Set | Allowed Next Status | Stock Change | Visible UI Behavior |
| --- | --- | --- | --- | --- |
| Not Started | System from outbound visibility | In Progress | None | Queue shows available picking review, no task evidence yet. |
| In Progress | Warehouse User | Submitted For Review, Closed, Cancelled | None | User can capture pick, pack, shortage, and evidence draft. |
| Submitted For Review | Warehouse User | Recount Requested / Repick Requested, Approved Clean, Approved Partial, Shortage Review, Pack Ready, Dispatch Handoff Ready, Escalated To Sales, Closed, Cancelled | None | User cannot edit unless manager requests repick; manager decision panel is active. |
| Recount Requested / Repick Requested | Warehouse Manager | In Progress, Submitted For Review, Closed, Cancelled | None | User sees manager note and updates pick evidence. |
| Approved Clean | Warehouse Manager | Pack Ready, Dispatch Handoff Ready, Delivery Draft Prepared, Closed, Cancelled | None | Clean pick evidence approved; delivery draft remains later policy. |
| Approved Partial | Warehouse Manager, with Sales policy where required | Shortage Review, Escalated To Sales, Pack Ready, Dispatch Handoff Ready, Delivery Draft Prepared, Closed, Cancelled | None | Partial pick approved for accepted dispatch quantity only. |
| Shortage Review | Warehouse Manager | Recount Requested / Repick Requested, Approved Partial, Escalated To Sales, Closed, Cancelled | None | Physical shortage is visible; no automatic Delivery Note. |
| Pack Ready | Warehouse Manager | Dispatch Handoff Ready, Delivery Draft Prepared, Closed, Cancelled | None | Packed evidence accepted; draft remains later policy. |
| Dispatch Handoff Ready | Warehouse Manager | Delivery Draft Prepared, Closed, Cancelled | None | Dispatch evidence ready; no shipment or stock posting occurs from task shell. |
| Escalated To Sales | Warehouse Manager | Recount Requested / Repick Requested, Approved Partial, Closed, Cancelled | None | Sales follow-up needed for customer-facing decision. |
| Delivery Draft Prepared | System after approved policy | Closed, Cancelled | None from task shell | A Delivery Note draft exists and remains unsubmitted. |
| Closed | Manager or System/Admin policy | None | None | Task is no longer active; audit remains visible to permitted roles. |
| Cancelled | Manager or System/Admin policy | None | None | Task is voided; audit remains visible to permitted roles. |

No W15D status posts stock. Delivery Note submission remains outside W15D and requires separate approval.

## 9. Manager Decision Matrix

| Situation | Recommended Manager Decision | Notes |
| --- | --- | --- |
| Picked quantity matches pending demand and no issue exists | Approve Clean Pick | Eligible for pack/dispatch handoff and later draft policy. |
| Warehouse user is unsure or location evidence is unclear | Request Repick/Recount | Manager note should explain what to verify. |
| Physical shortage found | Mark Shortage Review or Escalate To Sales | Sales may own customer-facing partial fulfillment decision. |
| Partial quantity is acceptable under policy | Approve Partial Pick | Draft policy may use accepted dispatch quantity only. |
| Damaged item found | Mark Shortage Review or Escalate To Sales | Damaged goods should not dispatch unless policy explicitly permits. |
| Item not found | Request Repick/Recount or Shortage Review | No automatic Delivery Note. |
| Wrong bin or unclear warehouse posture | Request Repick/Recount | Warehouse must not force dispatch against unclear warehouse context. |
| Substitution requested | Escalate To Sales | Substitution is not allowed by default. |
| Packed and dispatch documents are ready | Mark Dispatch Handoff Ready | Still no Delivery Note submit or stock posting. |

Sales owns customer communication, commercial partial shipment approval, customer promise changes, and Sales Order correction. Warehouse owns physical evidence and warehouse-side task posture.

## 10. Exception Policy

### Shortage

- Warehouse reports physical shortage.
- Shortage evidence must identify line, source warehouse, quantity short, and note.
- Manager may request repick, approve partial under policy, mark shortage review, or escalate to Sales.
- Sales/customer-facing decision is required for partial fulfillment when policy says.
- No automatic Delivery Note.

### Damage

- Evidence is required.
- Damaged goods must not dispatch unless a later approved policy explicitly allows it.
- Damage may trigger quarantine, return, claim, or quality process later.
- The task should preserve damage evidence and keep normal dispatch quantity separate.

### Not Found

- Requires repick/recount or manager review.
- Not-found quantity must not become accepted dispatch quantity.
- Repeated not-found posture should create a clear shortage or Sales escalation state.

### Substitution

- Not allowed by default.
- Requires Sales/customer approval and item policy.
- Warehouse Console must not silently replace the Sales Order item.

### Partial Fulfillment

- Requires manager approval.
- May require Sales approval depending on owner policy.
- Future draft should include accepted dispatch quantity only.
- Customer-facing communication remains Sales-owned.

## 11. Delivery Note Draft Policy Placeholder

Design only. Do not implement in W15D.

Delivery Note draft may later be prepared only when:

- Task status is `Approved Clean`, `Approved Partial`, `Pack Ready`, or `Dispatch Handoff Ready` under approved policy.
- Accepted for dispatch quantity is greater than zero.
- Sales and manager policy permits partial fulfillment where relevant.
- Required evidence is complete.
- Source warehouse is allowed.
- Sales Order line mapping is valid.
- Idempotency key is present.
- No blocked shortage, damage, substitution, or not-found issue remains unresolved.

Future Delivery Note draft behavior must:

- Create only an unsubmitted draft.
- Never call submit.
- Never post stock.
- Never return a native route.
- Return no valuation, accounting, or commercial fields.
- Append a custom Warehouse Picking Task Event.
- Keep Sales/Admin ownership explicit after draft creation.

Delivery Note submission remains outside W15D.

## 12. Stock Reservation And Pick List Policy

Default W15D policy:

- Do not create Pick List.
- Do not create Stock Reservation Entry.
- Do not reserve stock.
- Do not unreserve stock.
- Do not silently allocate stock from Warehouse Console.

If ERPNext Pick List or Stock Reservation integration is needed later, it must be a separate policy phase, such as W15D5 or W15D6. That phase must define role gates, source status, idempotency, audit events, stale-state handling, native-route containment, and protected smokes before implementation.

## 13. Audit And Idempotency Requirements

Every future outbound task action must write an audit event:

- Save pick draft.
- Submit for review.
- Request repick/recount.
- Manager approval.
- Partial approval.
- Shortage review.
- Sales escalation.
- Pack ready.
- Dispatch handoff ready.
- Future Delivery Note draft request.

Required audit fields:

- Actor.
- Timestamp.
- Previous status.
- Next status.
- Request id.
- Note.
- Policy version.
- Server validation result.

Idempotency rules:

- Same task and same request id must not append duplicate events.
- Same request id reused for another task must be rejected.
- Same request id reused for a different action must be rejected.
- Replayed requests must return the existing task state or draft reference when applicable.
- Failed writes must not create partial task state unless recoverable and audited.

## 14. UI Shell Plan

Future W15D2 UI shell should add an outbound workflow panel to Picking Review.

Recommended sections:

- Task status strip.
- Warehouse user pick/pack panel.
- Line-level pick evidence preview.
- Shortage, damage, not-found, substitution, and dispatch paperwork categories.
- Manager decision preview.
- Delivery draft policy preview.
- Read-only guardrail.

Suggested guardrail copy:

`No stock is reserved, picked, shipped, delivered, posted, or adjusted from this shell. Delivery Note draft and submit remain controlled later phases.`

Visible planned controls should be inert until backend action phases are approved. Do not add active buttons before server validation and tests exist.

## 15. Future Tests

Required tests for future implementation:

- Warehouse User can save pick draft without Delivery Note, Pick List, or Stock Reservation.
- Warehouse User cannot approve or release.
- Warehouse Manager can request repick.
- Warehouse Manager can approve clean pick only for clean lines.
- Warehouse Manager can approve partial only with shortage/discrepancy and policy.
- Warehouse Manager can escalate to Sales without touching Sales runtime.
- Damaged evidence is required.
- Not-found evidence is required.
- No Delivery Note creation in task draft/save or manager decision phases.
- No Delivery Note submission in any W15D phase.
- No Pick List creation.
- No Stock Reservation creation.
- No stock reserve/unreserve.
- No Stock Ledger entry.
- No native route is returned.
- No valuation or commercial fields are returned.
- Idempotent request does not duplicate events or drafts.
- Cross-task request id reuse is rejected.
- Mobile UI shell has no horizontal overflow.
- Sales protected boundary remains clean.
- Procurement protected boundary remains clean.

## 16. Open Owner Decisions

Owner decisions required before implementation:

1. Should Warehouse create internal Pick Tasks only, or also controlled Pick Lists later?
2. Should stock reservation ever be allowed from Warehouse Console?
3. Who approves partial shipment: Warehouse Manager, Sales Manager, or both?
4. Who owns customer notification for shortages?
5. Should pack/dispatch handoff create Delivery Note draft or only notify Sales/Admin?
6. Should Warehouse see Delivery Note draft reference as text/status only?
7. Is barcode scanning required in the first outbound implementation?
8. Is serial/batch scanning required in the first outbound implementation?
9. How should substitutions be handled?
10. How should multi-warehouse split picks be handled?
11. Who can close or cancel outbound tasks?
12. Should dispatch evidence require packing slip, carrier reference, driver name, or photo evidence?
13. Should partial pick approval require Sales confirmation before dispatch handoff?

## 17. Recommended Phase Split

Recommended W15D sequence:

- W15D1: docs/design owner approval.
- W15D2: Picking Review UI shell only, no backend writes.
- W15D3: internal Warehouse Picking Task draft/save backend.
- W15D4: manager review and outbound decision backend.
- W15D5: pack/dispatch handoff evidence and Sales escalation policy.
- W15D6: Delivery Note draft policy, only after Security/Stability and owner approval.
- Future: Delivery Note submission, only after a separate stock-posting design and approval.

Do not implement W15D runtime until Main Control issues a scoped implementation prompt.

## 18. Validation

Docs-only validation expected for this phase:

- `git diff --check HEAD`.
- Trailing whitespace check on changed docs.
- `git status --short --branch`.
