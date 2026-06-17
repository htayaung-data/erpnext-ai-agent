# Warehouse Console Phase W15C Inbound Receiving Workflow Design

Date: 2026-06-17

Status: `docs_only_receiving_workflow_design`

Decision: `consultant_policy_selected_ready_for_security_review`

Scope: docs-only design for a future controlled inbound receiving workflow. This document does not implement runtime code, backend methods, routes, smokes, tests, live alignment, Purchase Receipt creation, Purchase Receipt submission, stock posting, native ERPNext access, Sales runtime behavior, or Procurement runtime behavior.

## 0. Senior ERP Consultant Policy Decisions

Main Control selects the following default policies for W15C. These choices favor inventory accuracy, auditability, and clean Procurement/Warehouse separation over faster but riskier direct receiving execution.

1. Warehouse may prepare evidence and request a Purchase Receipt draft, but should not own Purchase Receipt submission.
2. A Purchase Receipt draft may be prepared only after Warehouse Manager approval and policy checks. The draft remains unsubmitted.
3. Procurement owns over-receipt approval, wrong-item supplier dispute, supplier return decision, PO correction, and commercial/supplier communication.
4. Warehouse Manager owns warehouse-side acceptance posture: clean receipt approval, recount, quarantine, damage review, and escalation decision.
5. Evidence is mandatory for damage, wrong item, overage, quarantine, and supplier paperwork mismatch before any backend action phase.
6. Short receipt can be approved by Warehouse Manager only within configured tolerance. Outside tolerance, it must escalate to Procurement.
7. Over receipt must not become draft-ready by Warehouse alone. It requires Procurement approval or explicit policy before accepted quantities are copied into a draft.
8. Damaged, wrong-item, rejected, and quarantine quantities must not be copied into normal accepted receipt draft lines unless a later quality/Procurement policy explicitly allows it.
9. One Purchase Order may support multiple receiving tasks for split deliveries, but only one active task per PO and target warehouse should be editable by a user at a time unless a manager overrides.
10. Warehouse access must be restricted by target warehouse. A user can receive only into warehouses allowed by server-side role/warehouse policy.
11. Procurement should receive a custom-console escalation signal when a task is escalated. Email/portal notifications are not part of W15C unless separately approved.
12. The first implementation should stay PO-based. ASN, shipment reference, serial/batch, barcode, and quality inspection integration are later enhancements.

## 1. Current State

Warehouse Console currently provides protected custom Warehouse routes for inbound receiving visibility and review:

- `/desk/warehouse-console-worklist/inbound-receiving`
- `/desk/warehouse-console-receiving/<purchase-order>`

The Inbound Receiving queue shows expected supplier arrivals from Purchase Order context and lets Warehouse users open a custom Receiving Review page. The Receiving Review page gives read-only Purchase Order receiving posture, line-level quantities, target warehouse context, and bounded receipt history where visible.

Current limitations:

- The flow is read-only only.
- There is no Warehouse Receiving Task record.
- Warehouse users cannot save a count draft.
- Warehouse users cannot submit a receiving case for manager review.
- Warehouse managers do not have an approval, recount, quarantine, or escalation decision workflow.
- There is no controlled Purchase Receipt draft preparation policy.
- The Warehouse Console does not create, submit, cancel, amend, post, receive, reconcile, reserve, or adjust stock documents.
- The Warehouse Console does not expose native ERPNext Purchase Receipt, Stock Entry, Stock Ledger, Stock Balance, or Purchase Order native form routes.

W15C designs the next controlled receiving workflow but does not start implementation.

## 2. Design Principles

The W15C inbound receiving workflow must follow these principles:

- No silent stock mutation. A Warehouse task can capture evidence and request review, but stock changes happen only through governed ERPNext stock documents.
- No direct Purchase Receipt submit action in the first implementation. Purchase Receipt submission remains blocked until a later separately approved execution phase.
- No native ERPNext route escape. All user-visible navigation stays inside custom Warehouse routes.
- Custom Warehouse routes only. The workflow should extend Receiving Review and possible future task routes, not link to native ERPNext forms or reports.
- Role-based controlled workflow. Warehouse User, Warehouse Manager, Procurement, and System/Admin responsibilities must be separate.
- Audit trail required. Each save, submit, recount request, manager decision, escalation, draft preparation request, and close event must leave a server-side event trail.
- Exception handling first. Shortage, overage, damaged goods, wrong item, missing warehouse, and uncertain counts must be visible as workflow states before any receipt draft is prepared.
- Procurement remains owner of PO and commercial terms. Warehouse owns physical receipt evidence, counts, damage notes, and warehouse-side acceptance posture.
- No valuation or commercial exposure. Warehouse receiving workflow must not show rates, amounts, taxes, landed cost, billing, payment, margins, supplier price, Item Price, or accounting fields.
- Server authority. The client can present controls, but the server must validate roles, permissions, status transitions, source documents, line quantities, and idempotency.

## 3. Roles

### Warehouse User

Warehouse User performs the physical receiving check.

Responsibilities:

- Open Inbound Receiving and Receiving Review.
- Start an arrival check when goods physically arrive.
- Confirm visible supplier, PO, target warehouse, and arrival date/time.
- Count item lines.
- Record received, damaged, short, over, accepted, rejected, or quarantine quantities.
- Add a receiving note.
- Add mandatory evidence reference for damage, wrong item, overage, quarantine, and supplier paperwork mismatch once backend actions are implemented.
- Save count draft when allowed.
- Submit the receiving task for manager review.

Forbidden:

- Approve the task.
- Prepare or submit Purchase Receipt outside the selected W15C policy and later approved ERPNext document governance.
- Change Purchase Order, supplier, commercial terms, rates, taxes, or payment context.
- Open native ERPNext forms or reports from Warehouse.
- Post stock, reconcile stock, reserve stock, or create stock documents.

### Warehouse Manager

Warehouse Manager reviews receiving tasks and decides the operational path.

Responsibilities:

- Review clean and discrepant arrivals.
- Approve clean receipt evidence.
- Approve discrepancy when policy allows.
- Request recount when counts are unclear.
- Mark quarantine or damage review when goods should not be accepted into normal stock.
- Escalate supplier, PO, or commercial issues to Procurement.
- Authorize controlled Purchase Receipt draft preparation only when the selected W15C policy allows it.
- Keep over-receipt, wrong item, supplier dispute, and PO correction under Procurement decision authority.

Forbidden in first W15C implementation:

- Submit Purchase Receipt.
- Post stock ledger changes.
- Override Procurement-owned supplier, price, terms, or PO commercial decisions.
- Use native ERPNext form or report escape from Warehouse.

### Procurement User / Manager

Procurement remains owner of supplier and PO commercial context.

Responsibilities:

- Maintain Purchase Orders.
- Own supplier coordination.
- Own supplier disputes, price/terms corrections, and PO commercial follow-up.
- Decide PO correction path when Warehouse reports a discrepancy that affects buying terms or supplier accountability.
- Approve or reject over-receipt acceptance before over quantities become draft-ready.
- Decide supplier return or supplier claim path for wrong, damaged, or disputed goods.

Procurement receives from Warehouse:

- Short receipt signal.
- Over receipt signal.
- Damaged or wrong item signal.
- Supplier paperwork issue signal.
- Evidence reference and receiving notes where policy allows.

Procurement does not need W15C Warehouse access unless a later cross-workspace review policy explicitly grants it.

### System/Admin

System/Admin configures workflow policy later.

Responsibilities:

- Configure roles and permitted warehouses.
- Configure discrepancy tolerance thresholds.
- Configure whether Purchase Receipt draft preparation is allowed.
- Configure manager approval policy, evidence requirements, and quarantine rules.
- Review security logs and workflow exceptions.

System/Admin is not a normal receiving operator.

## 4. Inbound Receiving Workflow

Use this daily operating flow:

1. Procurement creates or maintains a Purchase Order.
2. Warehouse sees expected supplier arrivals in Inbound Receiving.
3. Goods physically arrive at a warehouse.
4. Warehouse User opens Inbound Receiving.
5. Warehouse User opens Receiving Review for the Purchase Order.
6. Warehouse User starts arrival check.
7. Warehouse User confirms supplier, PO, target warehouse, and arrival date/time.
8. Warehouse User counts item lines.
9. Warehouse User records each line:
   - expected qty;
   - received qty;
   - damaged qty;
   - short qty;
   - over qty;
   - accepted qty;
   - rejected or quarantine qty.
10. Warehouse User adds receiving note and mandatory evidence reference when the case involves damage, wrong item, overage, quarantine, or supplier paperwork mismatch.
11. Warehouse User saves a count draft if more work is needed.
12. Warehouse User submits the receiving task for manager review.
13. Warehouse Manager reviews the task.
14. Warehouse Manager chooses one outcome:
   - approve clean receipt;
   - approve shortage within tolerance;
   - request recount;
   - quarantine or damage review;
   - escalate to Procurement;
   - request controlled Purchase Receipt draft preparation after policy checks.
15. Procurement decision is required for overage, wrong item, supplier dispute, PO correction, or commercial impact.
16. Only after approved policy can a controlled ERPNext Purchase Receipt draft be prepared.
17. No stock is posted from the W15C task shell.
18. No Purchase Receipt is submitted from the W15C task shell.

The workflow is evidence-first, review-second, and stock-document-later.

## 5. Page And Route Design

### Recommendation

Keep the existing Inbound Receiving queue as the entry point. Receiving Review should become the primary operational page because it already has Purchase Order, supplier, warehouse, line, and receipt-history context.

Add a future action panel inside Receiving Review rather than creating a separate first-step page. This keeps daily work simple:

- queue for prioritization;
- review page for one PO;
- task panel for controlled receiving work.

### Current Custom Routes

- `/desk/warehouse-console-worklist/inbound-receiving`
- `/desk/warehouse-console-receiving/<purchase-order>`

### Future Custom Route Candidate

If task detail becomes too large for the Receiving Review panel, add a future custom task route:

- `/desk/warehouse-console-receiving-task/<task-id>`

Use this route only after a Warehouse Receiving Task record exists. The route must remain custom Warehouse UI and must not expose native ERPNext Purchase Receipt, Purchase Order, or Stock Ledger pages.

### Why Not Native Purchase Receipt Route

Do not use native Purchase Receipt route directly because:

- native form route exposes ERPNext lifecycle controls and permissions outside the Warehouse Console contract;
- Warehouse users could confuse evidence capture with stock posting;
- Purchase Receipt may include valuation, tax, rate, landed cost, and commercial fields that Warehouse should not own;
- native form state does not provide Warehouse task-specific recount, quarantine, or manager-review audit semantics;
- protected Sales, Procurement, and Warehouse route governance requires custom managed routes for normal users.

## 6. Data Model Proposal

No implementation starts in W15C. The following model is a proposal for a later approved backend phase.

### Warehouse Receiving Task

Purpose: parent record for one controlled arrival check against a Purchase Order.

Candidate fields:

- `task_id`
- `purchase_order`
- `supplier`
- `target_warehouse`
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
- `created_by`
- `modified_by`

Rules:

- `supplier` and `target_warehouse` should be copied from server-visible PO context or validated against it.
- User and manager fields must be server-derived or server-validated.
- The task must not store rates, amounts, taxes, valuation, account, payment, or supplier pricing fields.

### Warehouse Receiving Task Line

Purpose: line-level physical receiving evidence.

Candidate fields:

- `task_id`
- `purchase_order_item`
- `item_code`
- `item_name`
- `uom`
- `expected_qty`
- `counted_qty`
- `accepted_qty`
- `damaged_qty`
- `short_qty`
- `over_qty`
- `quarantine_qty`
- `discrepancy_reason`
- `note`
- `target_warehouse`
- `line_status`

Rules:

- Server recomputes expected/open quantity from Purchase Order Item and existing receipt posture.
- Server validates that counted line belongs to the visible Purchase Order.
- Server rejects negative quantities and impossible combinations.
- `accepted_qty + damaged_qty + quarantine_qty` must follow the selected W15C policy and later configured tolerances.
- Over receipt must require manager review and possibly Procurement escalation.

### Audit / Event Log

Purpose: immutable workflow trace.

Candidate fields:

- `event_type`
- `actor`
- `timestamp`
- `task_id`
- `previous_status`
- `next_status`
- `note`
- `server_request_id`
- `source_ip_or_session_id` if policy allows.

Candidate event types:

- `started_arrival_check`
- `saved_count_draft`
- `submitted_for_review`
- `requested_recount`
- `approved_clean`
- `approved_with_discrepancy`
- `marked_quarantine_review`
- `escalated_to_procurement`
- `authorized_draft_preparation`
- `draft_prepared`
- `closed`
- `cancelled`

### Evidence / Attachment Placeholder

Future evidence support can include:

- photo reference;
- supplier delivery note reference;
- packing slip reference;
- damage report reference;
- internal receiving note reference.

Evidence is mandatory once backend actions are implemented for:

- damaged goods;
- wrong item;
- over receipt;
- quarantine;
- supplier paperwork mismatch.

Evidence remains optional for a clean receipt or simple short receipt inside tolerance unless policy later requires it. File handling must use standard Frappe attachment permissions and must not expose portal, email, or public file behavior without separate approval.

### Link Policy To ERPNext Purchase Receipt Draft

A Warehouse Receiving Task may later link to an ERPNext Purchase Receipt draft. It must not submit that document.

Candidate link fields:

- `purchase_receipt_draft`
- `draft_prepared_by`
- `draft_prepared_at`
- `draft_policy_version`

Rules:

- Draft creation requires W15C5 approval and the selected policy checks in this document.
- Draft creation must use server-side controlled methods.
- Draft creation must be idempotent.
- Draft submission remains blocked until later approval.
- Draft ownership after preparation should transfer to Procurement/Admin-controlled ERPNext document governance, not unrestricted Warehouse execution.

## 7. Status Model

Statuses are Warehouse task statuses, not ERPNext stock document statuses.

| Status | Who Can Set | Allowed Next Status | Stock Change | Visible UI Behavior |
| --- | --- | --- | --- | --- |
| Not Started | System from PO visibility | In Progress | None | Queue shows available receiving review, no task evidence yet. |
| In Progress | Warehouse User | Submitted For Review, Closed / Cancelled | None | Count draft panel is active; user can enter counts and notes. |
| Submitted For Review | Warehouse User | Recount Requested, Approved Clean, Approved With Discrepancy, Quarantine Review, Escalated To Procurement, Closed / Cancelled | None | User cannot edit counts unless manager requests recount; manager decision panel is active. |
| Recount Requested | Warehouse Manager | In Progress, Submitted For Review, Closed / Cancelled | None | User sees manager note and updates count evidence. |
| Approved Clean | Warehouse Manager | Draft Prepared, Closed / Cancelled | None | Clean receiving evidence approved; draft preparation may be available only in later phase. |
| Approved With Discrepancy | Warehouse Manager | Escalated To Procurement, Quarantine Review, Draft Prepared, Closed / Cancelled | None | Draft Prepared is allowed only for policy-approved discrepancy types. Overage, wrong item, damaged goods, quarantine, missing warehouse, and supplier paperwork mismatch require Procurement/policy resolution first. |
| Quarantine Review | Warehouse Manager | Recount Requested, Escalated To Procurement, Approved With Discrepancy, Closed / Cancelled | None | Goods should be treated as held or damaged; no stock posting occurs from task shell. |
| Escalated To Procurement | Warehouse Manager | Recount Requested, Approved With Discrepancy, Closed / Cancelled | None | Procurement follow-up needed for PO, supplier, or commercial issue. |
| Draft Prepared | System after approved policy | Closed / Cancelled | None from task shell | A Purchase Receipt draft exists, but not submitted. The task links to the draft if policy allows. |
| Closed / Cancelled | Warehouse Manager or System/Admin policy | None | None | Task is no longer active; audit remains visible to permitted roles. |

No status in W15C posts stock. The first possible ERPNext stock effect would be later Purchase Receipt submission outside W15C and only after separate owner approval.

## 8. Manager Decision Matrix

| Situation | Recommended Manager Decision | Notes |
| --- | --- | --- |
| Count matches PO and no damage | Approve Clean Receipt | Eligible for controlled draft preparation only after later policy approval. |
| Short received | Approve Discrepancy or Escalate To Procurement | Warehouse Manager may approve only inside tolerance; outside tolerance escalates to Procurement. |
| Over received | Hold excess and Escalate To Procurement | Over receipt needs Procurement approval or explicit policy before acceptance or draft preparation. Evidence is mandatory. |
| Damaged item | Quarantine Review | Manager decides whether to reject, quarantine, or request supplier/quality follow-up. |
| Wrong item | Quarantine Review and Escalate To Procurement | Do not accept wrong item as normal stock from Warehouse task shell. |
| Missing warehouse or unclear item posture | Request Recount or Request Correction | Warehouse must not force a receipt against unclear warehouse or line context. |
| User uncertainty | Request Recount | Manager note should explain what to recount or verify. |
| Supplier paperwork missing | Escalate To Procurement | Procurement owns supplier documentation and commercial follow-up. |
| Quality inspection required | Quarantine Review | Quality workflow remains separate unless later integrated. |

## 9. Integration With Procurement Console

Procurement owns:

- supplier communication;
- Purchase Order terms;
- supplier disputes;
- PO amendments or cancellations;
- price, tax, supplier policy, and payment context.

Warehouse owns:

- physical arrival evidence;
- counts;
- damage, wrong-item, shortage, overage, and quarantine signals;
- target warehouse receiving posture;
- manager review of warehouse-side evidence.

Warehouse should notify or escalate to Procurement when:

- shortage requires supplier follow-up;
- over receipt requires buying decision;
- damaged goods require supplier claim;
- wrong item was delivered;
- supplier paperwork is missing or mismatched;
- PO terms or lines need correction.

Do not duplicate Procurement approval flows. Warehouse should create a clear operational escalation, not a parallel supplier or commercial approval workflow.

For W15C policy, Procurement is the approving authority for over receipt, wrong-item supplier dispute, supplier return decision, and PO commercial correction. Warehouse Manager may recommend quarantine, reject, recount, or escalate, but should not independently convert these cases into accepted receipt drafts.

No commercial or valuation fields should appear in Warehouse receiving workflow. This includes rates, amounts, supplier price, taxes, landed cost, billing, payment, margin, and accounting fields.

## 10. Integration With ERPNext

Conceptual ERPNext mapping:

- Purchase Order is the source of expected inbound work.
- Purchase Order Item provides expected item, quantity, UOM, and target warehouse context when visible.
- Warehouse Receiving Task is a future custom controlled evidence record.
- Purchase Receipt draft is a later approved output, not a W15C shell action.
- Stock Ledger changes happen only after ERPNext Purchase Receipt submission, not during Warehouse task save, submit-for-review, approval, recount, quarantine, or escalation.

Stock Entry and Stock Reconciliation are not part of W15C receiving workflow. They may be considered only in separate approved designs for transfer, adjustment, or inventory-control workflows.

Quality Inspection may be referenced as read-only posture or future handoff only. W15C does not approve or reject Quality Inspection. Quarantine/damage decisions should remain Warehouse Manager decisions until a future Quality workflow is explicitly designed.

Serial, batch, barcode, and scan capture are not part of first W15C implementation unless later explicitly approved.

## 11. UX Design

### Inbound Receiving Queue

Existing row action remains:

- `Open receiving review`

The queue should stay focused on prioritization:

- due today;
- overdue;
- partially received;
- expected soon;
- supplier and warehouse context;
- clear empty states.

Do not add receiving execution controls directly in queue rows.

### Receiving Review Action Panel

Future panel placement: inside `/desk/warehouse-console-receiving/<purchase-order>`.

Suggested panel sections:

- Task status strip.
- Start arrival check.
- Count draft summary.
- Line count entry grid.
- Discrepancy panel.
- Manager decision panel.
- Read-only guardrail.

Allowed future labels:

- `Start arrival check`
- `Save count draft`
- `Submit for review`
- `Request recount`
- `Approve clean receipt`
- `Approve discrepancy`
- `Mark quarantine review`
- `Escalate to Procurement`
- `Prepare Purchase Receipt draft` only after W15C5 approval and selected policy checks.

Blocked labels in first implementation:

- `Receive`
- `Post`
- `Submit Purchase Receipt`
- `Create Purchase Receipt` unless a later draft-only policy is approved.
- `Submit`
- `Cancel`
- `Amend`
- `Reconcile`
- `Update Stock`

### User Task Line Entry

Use a compact count grid by line:

- item;
- expected qty;
- counted qty;
- accepted qty;
- damaged qty;
- short qty;
- over qty;
- quarantine qty;
- note.

The UI should show server-computed discrepancy summaries. The client should not be trusted as the source of truth.

### Discrepancy Panel

Use plain operational issue categories:

- short;
- over;
- damaged;
- wrong item;
- quarantine;
- missing warehouse;
- supplier paperwork issue;
- needs Procurement follow-up;
- needs recount.

### Read-only Guardrail

Guardrail copy should be visible on the receiving task shell:

> No stock is posted from this page. Purchase Receipt preparation and submission require a separate approved ERPNext document step.

Keep the language owner-facing and operational. Do not use developer or framework terms in visible UI.

### Empty, Unavailable, Restricted States

- Empty: no receiving task has been started for this Purchase Order.
- Unavailable: receiving workflow could not be loaded; refresh or contact an administrator.
- Restricted: user does not have access to receiving workflow for this Purchase Order or warehouse.
- Closed: task is closed; audit remains visible to authorized users.

### Mobile Constraints

Mobile receiving must support daily warehouse use:

- stacked line cards;
- large enough numeric inputs;
- one action group at a time;
- no horizontal scroll;
- sticky or repeated Save Draft only if later approved;
- no dense 4-column count grids on phone width;
- manager decisions should stack as cards.

## 12. Security And Hardening Requirements

Future implementation must include:

- Server-side role checks for every read, save, submit, and decision method.
- Server-side warehouse access checks.
- Server-side Purchase Order read permission checks.
- Server-side validation that task lines belong to the Purchase Order.
- Server-side validation that status transitions are allowed for the actor role.
- No client-trusted status transitions.
- CSRF protection through standard Frappe method behavior.
- Idempotency keys or server request identifiers for save, submit, manager decision, and draft preparation.
- Audit log for every status change and decision.
- Approved custom route whitelist only.
- Stale response protection in the client.
- No native ERPNext Form/List/Report route escape.
- No Quick Find direct write action.
- No valuation, accounting, price, tax, payment, billing, margin, or commercial exposure.
- No background job for Purchase Receipt draft unless separately approved and auditable.
- Strict field allowlists for task payloads.
- Length limits for notes and evidence references.
- Attachment policy before photo/document evidence is enabled.

## 13. Smoke And Test Plan

Future W15C tests should include:

- Warehouse User can open Receiving Review with receiving workflow shell visible.
- Warehouse User can start an arrival check in a source fixture.
- Warehouse User can enter count draft in a source fixture.
- Warehouse User can save count draft without creating Purchase Receipt.
- Warehouse User can submit receiving task for review.
- Warehouse User cannot approve, request draft preparation, or change manager decisions.
- Warehouse Manager can see manager decision panel.
- Warehouse Manager can approve clean receipt in shell-only or backend-task phase without stock posting.
- Warehouse Manager can approve discrepancy, request recount, mark quarantine review, or escalate to Procurement.
- Warehouse Manager cannot make over receipt draft-ready without Procurement/policy approval.
- Damage, wrong item, overage, quarantine, and supplier paperwork mismatch require evidence once backend actions exist.
- Manager actions stay shell-only until backend task phase is approved.
- No Purchase Receipt is created in W15C shell-only phase.
- No Purchase Receipt is submitted in any W15C phase.
- No native ERPNext route is exposed.
- No Stock Ledger, Stock Balance, Stock Entry, Stock Reconciliation, Delivery Note, Pick List, or Purchase Receipt native links appear.
- Status transitions are validated server-side.
- Stale task responses do not overwrite newer task state.
- Restricted users receive a controlled restricted state.
- Mobile count entry and manager decision cards have no horizontal overflow.
- Audit events are created for every saved draft, submit, and manager decision once backend exists.
- Sales and Procurement protected gates remain green when shared runtime is touched in later implementation.

## 14. Implementation Phasing Recommendation

Recommended sequence:

### W15C1: Docs/design policy approval

- Approve this workflow design and selected consultant policy.
- Decide only remaining configuration thresholds and warehouse access assignments.
- No runtime implementation.

### W15C2: UI shell only on Receiving Review

- Add visual receiving workflow shell inside Receiving Review.
- Show task status placeholder and future sections.
- No backend writes.
- No Purchase Receipt draft.
- No stock posting.

### W15C3: Internal receiving task backend draft/save

- Add Warehouse Receiving Task and Task Line backend records if approved.
- Implement save draft only.
- Add server validation and audit log.
- No manager approval yet.
- No Purchase Receipt draft.
- Add evidence placeholders and enforce mandatory evidence categories if backend actions are enabled.

### W15C4: Manager review/decision shell

- Add manager review panel and decision methods.
- Implement request recount, approve clean, approve discrepancy, quarantine review, escalate to Procurement.
- Add audit events.
- No Purchase Receipt submission.

### W15C5: Controlled Purchase Receipt draft policy

- Add server-controlled draft preparation only after security, operations, and Main Control approval.
- Draft creation must be idempotent and auditable.
- Draft must remain unsubmitted.
- Draft ownership after preparation follows Procurement/Admin ERPNext document governance.
- Exclude damaged, wrong-item, rejected, quarantine, unresolved overage, and unresolved supplier-dispute quantities from normal accepted draft lines unless a later approved policy explicitly permits them.

### W15C6: Hardening/security/operation review

- Review permission boundaries.
- Review audit logs.
- Review failure handling and rollback.
- Run focused smokes and protected workspace gates.
- Review live alignment and operational support steps.

## 15. Remaining Configuration Questions

The core policy is selected above. The remaining questions are configuration details for later implementation:

1. What exact short-receipt tolerance thresholds are acceptable before Procurement escalation is required?
2. Which users can receive into which target warehouses?
3. Should supplier delivery note or packing slip reference be mandatory for every receipt or only discrepancy cases?
4. Who may close or cancel a receiving task after it is submitted?
5. Which item categories require Quality Inspection handoff?
6. What should happen when Purchase Order line warehouse is missing or different from physical receiving warehouse?
7. What escalation notification channel should Procurement receive inside the custom console?
8. Should a manager be able to override the one-active-task-per-PO-and-warehouse rule for split deliveries?
9. What evidence retention period is required for photos or documents?
10. Which roles can view historical closed receiving task evidence?

## Recommended Next Step

Do not implement runtime yet. The recommended next step is Security/Stability design review of the selected W15C policy, followed by a W15C2 UI-shell implementation prompt if accepted.
