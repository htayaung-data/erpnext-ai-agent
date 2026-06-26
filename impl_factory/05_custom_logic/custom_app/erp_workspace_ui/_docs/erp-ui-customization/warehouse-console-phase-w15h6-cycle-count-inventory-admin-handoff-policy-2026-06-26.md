# Warehouse Console Phase W15H6 Cycle Count Inventory/Admin Handoff Policy

Date: 2026-06-26

Status: docs-only handoff policy. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, pushes, Stock Reconciliation behavior, Stock Entry behavior, stock mutation, native ERPNext route exposure, valuation/accounting/commercial exposure, Sales runtime changes, Procurement runtime changes, notification behavior, email, portal access, or external actions.

Related baseline:

- W15H1 Cycle Count / Inventory Variance Workflow Design.
- W15H3 custom Cycle Count Task metadata.
- W15H4 custom Cycle Count Task draft-save backend.
- W15H5 custom Cycle Count Task manager decision backend.
- W15G6/W15G8 request-only Inventory/Admin handoff pattern for internal transfer.

## 1. Purpose

W15H6 defines the policy boundary for a future Inventory/Admin handoff after Warehouse cycle count manager review.

The core decision is:

- Warehouse may record physical count evidence and manager variance posture.
- Warehouse may request Inventory/Admin review later through custom request/status records.
- Warehouse must not create, save, submit, cancel, amend, or route to Stock Reconciliation or Stock Entry.
- Inventory/Admin owns any future stock adjustment document governance.

W15H6 is not runtime approval. It is the required owner/security policy layer before W15H7 metadata and W15H8 backend handoff work.

## 2. Current Source Posture

W15H3-W15H5 provide custom internal records and backend methods only:

- `Warehouse Cycle Count Task`
- `Warehouse Cycle Count Task Line`
- `Warehouse Cycle Count Task Event`
- `save_warehouse_cycle_count_task_draft(...)`
- `save_warehouse_cycle_count_manager_decision(...)`

The current backend writes only custom task status/event rows. It does not adjust stock, create ERPNext stock documents, expose native ERP routes, or expose valuation/accounting/commercial payloads.

W15H5 manager decisions remain internal Warehouse posture only:

- `Recount Requested`
- `Clean Count`
- `Variance Review`
- `Quarantine Review`
- `Serial/Batch Review`
- `Inventory/Admin Review Requested`
- `Rejected`
- `Cancelled`
- `Closed`

These statuses are not stock adjustment, document approval, posting, valuation review, accounting approval, or native ERPNext workflow execution.

## 3. Recommended Handoff Model

Recommended next runtime model:

- Create a custom request/status record only.
- Default status: `Requested`.
- The request is created from a reviewed custom `Warehouse Cycle Count Task`.
- Lines are derived from the source task, not arbitrary client-provided rows.
- The request carries plain text/status references only.
- Response payload must keep all stock/document/accounting side-effect flags false.

Recommended future DocTypes:

- `Warehouse Inventory Variance Handoff Request`
- `Warehouse Inventory Variance Handoff Request Line`
- `Warehouse Inventory Variance Handoff Request Event`

All records should be custom `ERP Workspace UI` records, non-submittable, not web-indexed, with no native route links, no ERPNext document Link fields, and no attachment or HTML fields unless later security review approves them.

## 4. Handoff Types

Recommended request-only handoff types:

- `variance_adjustment_policy_review`: Inventory/Admin review of variance evidence and adjustment policy. Request only; no adjustment created.
- `stock_reconciliation_policy_review`: Inventory/Admin review of whether a future Stock Reconciliation process is appropriate. Request only; no Stock Reconciliation draft created.
- `recount_policy_review`: review of whether recount is sufficient or more evidence is needed.
- `quarantine_quality_review`: quality or restricted-stock review for quarantine/damage posture.
- `serial_batch_policy_review`: serial/batch mismatch or restricted tracking review.
- `location_policy_review`: source/location/scope policy review.
- `close_or_cancel_review`: administrative review for rejected, cancelled, or closed count tasks.

Owner-facing UI must render business labels, not raw keys. Examples:

- `variance_adjustment_policy_review` -> "Variance policy review requested - no stock adjusted".
- `stock_reconciliation_policy_review` -> "Stock Reconciliation policy review requested - no draft created".
- `serial_batch_policy_review` -> "Serial/batch review requested - no stock posted".

## 5. Allowed Source States

Default allowed source `count_status` values:

- `Variance Review`
- `Quarantine Review`
- `Serial/Batch Review`
- `Inventory/Admin Review Requested`
- `Rejected`
- `Cancelled`
- `Closed`

Optional source state:

- `Clean Count` may create `close_or_cancel_review` only if Inventory/Admin wants closure audit, but it must not imply adjustment.

Blocked source states:

- `Planned`
- `Count In Progress`
- `Submitted For Review`
- `Recount Requested`

Rationale: handoff should happen only after manager posture exists. Draft/in-progress counts and recount requests are not ready for Inventory/Admin governance.

## 6. Eligibility Rules

Future handoff creation should require:

- Authenticated user.
- Server-side manager role gate: `Warehouse Manager`, `Stock Manager`, or `System Manager`.
- Existing visible custom Cycle Count Task.
- Source task has warehouse context.
- Source task has at least one line.
- Source status is allowed for the requested handoff type.
- Handoff note is required.
- Request id is required.
- Idempotency hash covers task id, source status, handoff type, note/reference fields, and derived lines.
- Same request id plus same payload returns the existing request.
- Same request id plus changed payload rejects.
- Same request id reused across another task rejects.

Lines should be derived from the custom task and should include only evidence/status fields needed for review:

- task line reference;
- item identity;
- warehouse;
- location reference text;
- UOM;
- counted quantity;
- variance quantity;
- variance direction;
- condition grade;
- reason code;
- evidence reference;
- serial/batch reference text;
- line status.

## 7. Exclusion Rules

Future handoff creation must reject:

- Missing task id.
- Missing request id.
- Missing handoff note.
- Unknown handoff type.
- Draft/in-progress/recount source states.
- Source task with no lines.
- Source task without visible warehouse.
- Line warehouse mismatch.
- Line without item identity.
- Native ERP route need.
- Any request to create, save, submit, cancel, amend, route to, or link to Stock Reconciliation.
- Any request to create, save, submit, cancel, amend, route to, or link to Stock Entry.
- Any request to reserve, unreserve, post, reconcile, or mutate stock.
- Any request to expose valuation/accounting/commercial fields.
- Any request to send notification, email, portal, customer, supplier, Sales, or Procurement actions.

## 8. Explicitly Blocked Behavior

W15H6 blocks:

- Stock Reconciliation draft creation.
- Stock Reconciliation save.
- Stock Reconciliation submit.
- Stock Reconciliation cancel.
- Stock Reconciliation amend.
- Stock Entry draft creation.
- Stock Entry save.
- Stock Entry submit.
- Stock Entry cancel.
- Stock Entry amend.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Reservation creation.
- Reserve stock.
- Unreserve stock.
- Stock movement.
- Stock posting.
- Bin update.
- Item update.
- Warehouse update.
- Native ERPNext route exposure.
- `/app`
- `/desk/Form`
- `/desk/List`
- `/desk/Report`
- `/desk/query-report`
- Valuation fields.
- Accounting fields.
- Commercial fields.
- Rate, amount, price, tax, cost, margin, profit, landed cost, debit, credit, payable, GL, payment, billing.
- Sales runtime changes.
- Procurement runtime changes.
- Notification, email, portal, customer-facing, supplier-facing, or external action.

## 9. Reference Visibility

Default rule:

- Any future Stock Reconciliation or Stock Entry reference remains blocked.

If a later owner/security phase allows references, they must be:

- plain text/status only;
- not clickable links;
- not `Link` or `Dynamic Link` DocType fields;
- not native route URLs;
- not route-bearing HTML;
- not file/attachment fields;
- not visible to roles outside the approved Warehouse/Inventory/Admin context.

No native-submit bypass containment exists yet for cycle count adjustment documents, so native document references should remain blocked by default.

## 10. Role Ownership

Warehouse User / Stock User:

- Records physical count evidence in the custom task only.
- Does not create handoff request.
- Does not adjust stock.

Warehouse Manager / Stock Manager:

- Reviews count evidence.
- Creates request-only Inventory/Admin handoff later if approved.
- Does not create or submit ERPNext adjustment documents.

Inventory/Admin:

- Owns future adjustment policy.
- Owns any future Stock Reconciliation governance.
- Owns native-submit containment if ERPNext documents are ever introduced.

Finance/Admin:

- Enters only if valuation/accounting/write-off policy is separately approved.
- No Finance/Admin runtime is approved by W15H6.

Sales and Procurement:

- Not normal owners of inventory variance.
- No Sales or Procurement runtime behavior is approved.

## 11. Future Test Requirements

Before any runtime handoff phase, tests should prove:

- Manager role allowlist only.
- Warehouse User and Stock User denied.
- Handoff type allowlist.
- Source-state to handoff-type mapping.
- Handoff note required.
- Request id required.
- Lines derived from the source task.
- Changed-payload idempotency rejection.
- Cross-task request id reuse rejection.
- No Stock Reconciliation creation/save/submit/cancel/amend.
- No Stock Entry creation/save/submit/cancel/amend.
- No Stock Ledger mutation.
- No Stock Balance mutation.
- No Stock Reservation/reserve/unreserve.
- No stock posting or movement.
- No native route exposure.
- No valuation/accounting/commercial payload.
- No Sales/Procurement runtime change.
- No notification/email/portal behavior.

## 12. Owner Decisions Before W15H7/W15H8 Runtime

Open decisions:

- Which manager statuses can create each handoff type.
- Whether `Clean Count` should ever create closure audit handoff.
- Whether Inventory/Admin handoff is required for all variance lines or only above tolerance.
- Whether tolerance policy is item/category/warehouse specific.
- Whether serial/batch mismatches always require Inventory/Admin review.
- Whether quarantine/damage posture requires Quality role participation later.
- Whether plain text Stock Reconciliation references are ever allowed.
- Whether native-submit bypass containment is possible before Stock Reconciliation runtime.
- Who can close or cancel a variance handoff request.

Default until decided:

- request-only custom records;
- no Stock Reconciliation draft;
- no Stock Entry draft;
- no stock mutation;
- no native route;
- no valuation/accounting/commercial exposure.

## 13. Recommendation

Proceed next to metadata-only `W15H7 Warehouse Inventory Variance Handoff Request` DocTypes if owner/security accepts this policy.

Do not implement Stock Reconciliation draft behavior in W15H7 or W15H8. The next runtime step should be request-only custom handoff creation, equivalent to the W15G internal transfer handoff pattern.
