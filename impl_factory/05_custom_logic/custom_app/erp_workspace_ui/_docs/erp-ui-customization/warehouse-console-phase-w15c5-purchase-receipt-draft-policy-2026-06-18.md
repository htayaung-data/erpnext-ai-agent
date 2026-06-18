# Warehouse Console Phase W15C5 Purchase Receipt Draft Policy

Date: 2026-06-18

Status: docs-only Warehouse design artifact. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, or pushes.

Related baseline:

- W15C2 receiving workflow UI shell.
- W15C3 internal Warehouse Receiving Task draft/save backend.
- W15C4 manager decisions on custom Warehouse Receiving Task records.
- `warehouse-console-phase-w15c-inbound-receiving-workflow-design-2026-06-17.md`.
- `warehouse-console-phase-w11b-purchase-receipt-receiving-execution-design-2026-05-31.md`.

## 1. Objective

W15C5 defines the policy for a future controlled Purchase Receipt draft preparation step from an approved Warehouse Receiving Task.

The future W15C5 runtime objective, if later approved, is limited to preparing an unsubmitted Purchase Receipt draft after controlled Warehouse evidence and manager approval. The draft is an ERPNext document and must be treated as a mutation. It is not stock posting approval.

W15C5 must not:

- Submit Purchase Receipt.
- Post stock.
- Create Stock Ledger entries.
- Expose native ERPNext Purchase Receipt form, list, report, or workspace routes to normal Warehouse users.
- Expose valuation, rates, taxes, accounts, landed cost, payment, billing, supplier pricing, or commercial fields.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.

## 2. Allowed Source State

A future draft-preparation method may proceed only when all of these are true:

- The source is a custom `Warehouse Receiving Task`.
- The task belongs to a submitted, receiving-open Purchase Order that remains visible to Warehouse.
- The Purchase Order is not closed, cancelled, stopped, or otherwise blocked for receiving.
- The task status is `Approved Clean`.
- Or the task status is `Approved With Discrepancy` and the configured policy explicitly permits the included accepted quantities.
- The task has at least one line with accepted quantity greater than zero.
- Required evidence exists for damaged, wrong item, overage, quarantine, supplier paperwork mismatch, or any other evidence-required exception.
- Every included line matches a server-visible Purchase Order Item.
- Every included line belongs to the selected target warehouse or a policy-approved receiving warehouse.
- The actor has a manager-level Warehouse role and any future configured warehouse scope.
- The request carries a server-enforced idempotency key.

Allowed manager roles for requesting draft preparation should be:

- Warehouse Manager.
- Stock Manager.
- System Manager where operational policy allows.

Warehouse User and Stock User may view the approved task result if permitted, but must not prepare the draft.

## 3. Blocked Source State

Draft preparation must be blocked for these task statuses:

- `Not Started`.
- `In Progress`.
- `Submitted For Review`.
- `Recount Requested`.
- `Quarantine Review`.
- `Escalated To Procurement`.
- `Closed`.
- `Cancelled`.
- `Draft Prepared`, unless the call is an idempotent replay returning the existing draft reference.

Draft preparation must also be blocked when:

- No manager approval exists.
- Evidence required by policy is missing.
- Accepted quantities are zero.
- Task lines do not match Purchase Order lines.
- Target warehouse is missing or not allowed.
- The Purchase Order line is missing, closed, cancelled, received in full, or not visible to Warehouse.
- There is unresolved overage.
- There is unresolved wrong-item evidence.
- There is unresolved quarantine evidence.
- There is unresolved supplier dispute.
- There is supplier paperwork mismatch not resolved by Procurement policy.
- A duplicate draft already exists for the task and is not an idempotent replay.

## 4. Line Inclusion Policy

Normal Purchase Receipt draft lines may include only approved accepted quantities for normal receipt.

Use accepted quantity as the draft quantity. Do not use counted quantity when counted and accepted differ.

Explicitly exclude from normal draft lines:

- Damaged quantity.
- Wrong-item quantity.
- Rejected quantity.
- Quarantine quantity.
- Unresolved overage.
- Unresolved supplier dispute quantity.
- Unresolved supplier paperwork mismatch quantity.
- Any line without a valid Purchase Order Item mapping.
- Any line not belonging to the selected target warehouse or policy-approved receiving warehouse.

If all lines are excluded, the draft preparation must be blocked with a business-safe reason.

## 5. Over-Receipt Policy

Over-receipt cannot become draft-ready by Warehouse approval alone.

Default W15C5 policy:

- Exclude over quantity from the draft.
- Require Procurement approval or an explicitly configured over-receipt policy before any over quantity can become draft-ready.
- Keep over-receipt evidence attached to the Warehouse Receiving Task.
- Keep the task blocked or escalated if the only meaningful quantity is unresolved overage.

Owner approval is required before any future implementation may include over quantity in a Purchase Receipt draft.

## 6. Discrepancy Policy

For `Approved With Discrepancy`:

- Short receipt within tolerance may be draft-ready for accepted quantity only.
- Accepted quantity can be drafted when the manager approval and configured policy allow it.
- Damaged quantity must not be drafted as normal stock.
- Quarantine quantity must not be drafted as normal stock.
- Wrong item quantity must not be drafted as normal stock.
- Procurement-owned issues remain blocked until Procurement resolves them.
- Supplier paperwork mismatch remains blocked unless policy says the accepted quantity may proceed.
- The future draft method must use server-computed line eligibility, not client-selected line eligibility.

## 7. Role And Ownership Model

Warehouse User / Stock User:

- Cannot prepare Purchase Receipt drafts.
- Can view task result and draft status only if policy permits.
- Cannot submit Purchase Receipt.
- Cannot override Procurement-owned issues.

Warehouse Manager / Stock Manager:

- May request draft preparation only after approval conditions are satisfied.
- Cannot submit Purchase Receipt.
- Cannot override Procurement-owned supplier, PO, over-receipt, wrong-item, supplier-return, or commercial decisions.
- Must receive a clear blocked state when policy conditions are not satisfied.

Procurement / Admin:

- Owns the Purchase Receipt draft after creation.
- Owns Purchase Receipt submit.
- Owns supplier terms, PO correction, supplier dispute, supplier return, and commercial resolution.
- May need a future review queue or notification, but that is not implemented in W15C5 design.

System Manager:

- May configure draft policy.
- May configure warehouse scope, tolerance thresholds, draft owner, and native-submit containment.

## 8. Future Backend Method Proposal

Design only. Do not implement in this phase.

Suggested future method:

```python
prepare_warehouse_receiving_purchase_receipt_draft(task_id, request_id)
```

The method must:

- Require authentication.
- Require manager-level Warehouse role.
- Validate configured warehouse scope.
- Load only the custom `Warehouse Receiving Task`.
- Validate task status.
- Validate task lines against Purchase Order lines server-side.
- Validate accepted quantities.
- Validate target warehouse.
- Validate evidence requirements.
- Enforce the exclusion policy.
- Reject client-supplied valuation, rate, amount, tax, account, supplier pricing, native route, submit, cancel, amend, or print/email fields.
- Use `request_id` for idempotency.
- Create only one unsubmitted Purchase Receipt draft if later approved.
- Never call submit.
- Append a Warehouse Receiving Task Event.
- Set task status to `Draft Prepared` only after the draft is successfully created.
- Store a draft reference only after successful creation.
- Return a bounded safe payload.
- Return no native ERPNext route.
- Return no valuation or commercial fields.

The method must not:

- Submit Purchase Receipt.
- Create Stock Ledger Entry.
- Call Stock Entry.
- Call Stock Reconciliation.
- Update Procurement Console runtime.
- Update Sales Console runtime.
- Send email, portal notification, or background job unless a later design explicitly approves it.

## 9. Idempotency Policy

Draft preparation must be idempotent.

Rules:

- Same task and same `request_id` returns the same prepared draft reference if the draft was already prepared.
- Same task with an existing draft must not create another Purchase Receipt draft.
- Same `request_id` reused for another task must be rejected.
- Same `request_id` reused with different source state or requested operation must be rejected.
- If draft creation succeeds but response delivery fails, replay must return the existing draft reference.
- If draft creation fails before the ERPNext draft exists, replay may try again only after confirming no draft was created.
- The event log must record idempotent replay separately from first creation.

## 10. Audit Events

Future event types:

- `authorized_draft_preparation`.
- `draft_preparation_blocked`.
- `draft_prepared`.
- `draft_prepare_idempotent_replay`.

Each event should include:

- Actor.
- Timestamp.
- Previous status.
- Next status.
- Policy version.
- Server request id.
- Note.
- Block reason when blocked.
- Draft reference only if a draft exists.

Audit rules:

- Do not silently clean up or overwrite draft references.
- Do not remove evidence after draft preparation.
- Do not store valuation, rates, taxes, accounts, billing, payment, or supplier pricing in the Warehouse task event.
- Blocked attempts should be auditable when they represent a policy decision, but should not expose stack traces or internal errors.

## 11. ERPNext Document Field Mapping

Safe minimal mapping for a future unsubmitted draft:

- Purchase Order.
- Supplier, derived from Purchase Order.
- Target warehouse.
- Item code.
- Purchase Order Item.
- Accepted quantity.
- UOM.

The future method must derive these server-side from the task and Purchase Order context. The client must not provide trusted ERPNext document fields.

Explicitly forbidden in Warehouse payload and UI:

- Rate.
- Amount.
- Tax.
- Account.
- Valuation rate.
- Stock value.
- Landed cost.
- Price list.
- Payment terms.
- Billing terms.
- Supplier quotation fields.
- Supplier commercial fields.
- GL fields.
- Cost, profit, or margin fields.
- Native route targets.

## 12. UI Behavior Design

Design only. Do not implement in this phase.

Receiving Review or the receiving task panel may show:

- `Draft preparation available` only after task approval and policy readiness.
- `Request draft preparation` only for manager-level roles and only when policy-ready.
- `Draft prepared` only after backend confirms a draft exists.
- `Draft remains unsubmitted` guardrail.
- Safe blocked reasons when draft preparation is not available.

The UI must not expose:

- Native Purchase Receipt route.
- Submit button.
- Print button.
- Email button.
- Share or portal controls.
- Valuation fields.
- Accounting fields.
- Commercial fields.

The UI should keep users inside custom Warehouse routes. If a prepared draft reference is visible to Warehouse, it should be a safe identifier or status marker, not a native link.

## 13. Failure Handling

Future implementation must return business-safe failure states:

- `policy_blocked`.
- `task_not_approved`.
- `evidence_missing`.
- `overage_unresolved`.
- `wrong_item_unresolved`.
- `quarantine_unresolved`.
- `supplier_dispute_unresolved`.
- `target_warehouse_not_allowed`.
- `duplicate_draft_exists`.
- `po_closed_or_cancelled`.
- `purchase_order_line_mismatch`.
- `permission_denied`.
- `idempotency_conflict`.

Failure response rules:

- No stack trace.
- No SQL.
- No native route.
- No valuation or commercial data.
- No ERPNext document submission.
- No partial Purchase Receipt draft unless explicitly audited and recoverable.

## 14. Future Tests

Required tests for any future W15C5 implementation:

- Approved clean task can prepare one unsubmitted draft.
- In-progress task is blocked.
- Submitted-for-review task is blocked until manager approval.
- Recount-requested task is blocked.
- Quarantine-review task is blocked.
- Escalated-to-Procurement task is blocked.
- Approved discrepancy includes accepted quantity only.
- Damaged quantity is excluded.
- Quarantine quantity is excluded.
- Wrong item quantity is excluded.
- Overage is excluded unless policy-approved.
- Purchase Receipt is never submitted.
- Stock Ledger entry is not created by W15C5.
- Native route is not returned.
- Valuation and commercial fields are not returned.
- Manager role is required.
- Warehouse User is denied.
- Idempotent request does not duplicate draft.
- Cross-task request id reuse is rejected.
- Audit event is appended.
- Duplicate draft is not created when a previous draft exists.
- Sales protected boundary remains clean.
- Procurement protected boundary remains clean.

## 15. Open Owner Decisions

Owner decisions required before runtime implementation:

1. Should Warehouse Manager be allowed to prepare the draft, or only request draft preparation for Procurement/Admin?
2. Should draft creation happen immediately after manager request, or require Procurement confirmation?
3. What shortage tolerance is acceptable before Procurement escalation is required?
4. Is over-receipt ever allowed into a draft?
5. If over-receipt is allowed later, which Procurement approval proves it?
6. Should quarantine stock ever be drafted into a quarantine warehouse?
7. Who can close or cancel receiving tasks?
8. Should draft reference be visible to Warehouse users without native route access?
9. Who owns abandoned or stale prepared drafts?
10. How should native-submit bypass be prevented for generated drafts?
11. Should supplier delivery note or packing slip reference be mandatory before draft preparation?
12. Which item categories require Quality Inspection before draft preparation?

## 16. Recommendation

Do not implement W15C5 runtime yet.

Recommended next step:

1. Owner decides whether W15C5 is draft preparation by Warehouse Manager or only a request to Procurement/Admin.
2. Security/Stability reviews native-submit containment and idempotency.
3. Operation Reviewer confirms line inclusion and discrepancy policy.
4. Main Control issues a source-only implementation prompt only after those decisions are explicit.

Until then, W15C5 remains a design package only. Purchase Receipt draft creation, Purchase Receipt submission, stock posting, native ERP route exposure, valuation/accounting exposure, Quick Find/Search write actions, Sales runtime changes, and Procurement runtime changes remain blocked.

## 17. Validation

Docs-only validation expected for this phase:

- `git diff --check HEAD`.
- Trailing whitespace check on changed docs.
- `git status --short --branch`.
