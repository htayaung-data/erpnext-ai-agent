# Warehouse Console Phase W15H9 Cycle Count Stock Reconciliation Draft Policy

Date: 2026-06-26

Status: docs-only Stock Reconciliation draft policy gate. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, pushes, Stock Reconciliation behavior, Stock Entry behavior, stock mutation, native ERPNext route exposure, valuation/accounting/commercial exposure, Sales runtime changes, Procurement runtime changes, notification behavior, email, portal access, or external actions.

Related baseline:

- W15H1 Cycle Count / Inventory Variance Workflow Design.
- W15H2 Cycle Count / Inventory Variance overview UI shell.
- W15H3 custom Warehouse Cycle Count Task metadata.
- W15H4 custom Warehouse Cycle Count Task draft-save backend.
- W15H5 custom Warehouse Cycle Count Task manager decision backend.
- W15H6 Cycle Count Inventory/Admin Handoff Policy.
- W15H7 custom Warehouse Inventory Variance Handoff Request metadata.
- W15H8 request-only Inventory/Admin variance handoff backend.

## 1. Title And Scope

W15H9 defines the policy boundary for any future cycle-count Stock Reconciliation draft phase.

This is a policy gate only. It does not approve Stock Reconciliation draft creation. It does not approve Stock Reconciliation submission. It does not approve Stock Entry creation, stock movement, Stock Ledger mutation, Stock Balance mutation, Stock Reservation, reserve/unreserve actions, native ERPNext route exposure, valuation/accounting/commercial exposure, Sales runtime changes, Procurement runtime changes, notification behavior, email, portal access, or external actions.

The purpose is to document what must be true before Main Control may even consider a later runtime phase that prepares an unsubmitted Stock Reconciliation draft from a reviewed inventory variance handoff.

W15H9 must not:

- Create Stock Reconciliation.
- Save Stock Reconciliation.
- Submit Stock Reconciliation.
- Cancel Stock Reconciliation.
- Amend Stock Reconciliation.
- Delete Stock Reconciliation.
- Create Stock Entry.
- Save Stock Entry.
- Submit Stock Entry.
- Cancel Stock Entry.
- Amend Stock Entry.
- Delete Stock Entry.
- Create or mutate Stock Ledger.
- Create or mutate Stock Balance.
- Create or mutate Stock Reservation.
- Reserve stock.
- Unreserve stock.
- Adjust stock quantity.
- Post stock.
- Expose native Stock Reconciliation routes.
- Expose native Stock Entry routes.
- Expose `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report` native route patterns.
- Expose valuation, accounting, billing, payment, tax, landed cost, margin, profit, rate, amount, price, cost, debit, credit, payable, GL, or commercial fields.
- Update Item, Bin, Warehouse, Sales Order, Purchase Order, Delivery Note, Purchase Receipt, Purchase Invoice, Pick List, Material Request, or Stock Entry.
- Trigger customer notification.
- Trigger supplier notification.
- Send email.
- Open portal access.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.

## 2. Current W15H State

The current cycle count / inventory variance workflow is bounded to custom Warehouse evidence, manager posture, and request-only Inventory/Admin handoff.

Current state:

- W15H4 saves custom `Warehouse Cycle Count Task` draft evidence.
- W15H5 saves custom manager decisions on the task.
- W15H8 creates custom `Warehouse Inventory Variance Handoff Request` records.
- W15H8 writes only custom request parent, line, and event rows.
- W15H8 does not create Stock Reconciliation drafts.
- W15H8 does not create Stock Entry drafts.
- W15H8 does not adjust or post stock.
- W15H8 does not expose native ERPNext routes.
- W15H8 keeps valuation hidden and stock-effect flags false.

The current approved endpoint is request-only Inventory/Admin handoff. Any Stock Reconciliation draft is a future decision, not a current capability.

## 3. Business Flow In Plain English

Cycle count governance has three separate stages.

Warehouse evidence stage:

- Warehouse records count source, count scope, warehouse, item, counted quantity, variance posture, reason, condition, serial/batch reference, and evidence.
- Warehouse Manager or Stock Manager reviews the physical count evidence.
- The result is clean count, variance review, quarantine review, serial/batch review, Inventory/Admin review request, rejection, cancellation, or closure posture only.

Inventory/Admin review stage:

- Inventory/Admin reviews whether a variance can be accepted, rejected, recounted, quarantined, or escalated.
- Inventory/Admin reviews adjustment policy, tolerance policy, serial/batch scope, location policy, and native-submit containment.
- The result may be a decision to reject, close, request more evidence, request recount, or prepare a future unsubmitted draft under explicit policy.

ERPNext stock adjustment document stage:

- ERPNext Stock Reconciliation draft creation, review, submit, cancel, amend, and posting are separate high-risk lifecycle actions.
- Stock posting affects Stock Ledger and Stock Balance.
- This stage must remain outside Warehouse until owner/security approval exists.

W15H9 governs only the policy between the second and third stages. It does not start the third stage.

## 4. Recommended Default

Default recommendation: keep Stock Reconciliation draft creation blocked.

If the owner later approves a draft phase, the safest default is Inventory/Admin-owned preparation of an unsubmitted Stock Reconciliation draft only. Warehouse should request review and provide evidence, but Warehouse should not directly create, open, submit, cancel, amend, or post Stock Reconciliation.

Recommended default ownership:

- Warehouse User: no Stock Reconciliation draft rights from Warehouse Console.
- Stock User: no Stock Reconciliation draft rights from Warehouse Console.
- Warehouse Manager: may request policy review only.
- Stock Manager: may request policy review only unless owner explicitly grants draft preparation.
- Inventory/Admin or System Manager: owns future draft governance.
- ERPNext native Stock Reconciliation submit remains outside Warehouse Console.

Rejected default:

- Direct Warehouse Stock Reconciliation creation or submission from Warehouse Console.
- Native Stock Reconciliation route links for Warehouse users.
- Warehouse-visible valuation/accounting fields.
- Auto-posting or background Stock Reconciliation submission.
- Silent stock adjustment from cycle count evidence.

## 5. Future Draft Eligibility

A future Stock Reconciliation draft phase must require all of the following before draft creation is considered:

- Existing custom `Warehouse Inventory Variance Handoff Request`.
- Handoff status must be explicitly approved by Inventory/Admin in a future phase, not merely `Requested`.
- Handoff type must be `stock_reconciliation_policy_review`, `variance_adjustment_policy_review`, or another owner-approved adjustment policy type.
- Source cycle count task must be manager reviewed.
- Source warehouse must be visible and allowed by policy.
- Source lines must be derived from the custom handoff request or source task, not arbitrary client rows.
- Variance quantity, counted quantity, variance direction, condition, reason, and evidence must be internally consistent.
- Positive variance, negative variance, zero count, missing item, unexpected item, quarantine, serial/batch, and blocked lines must have explicit policy outcomes.
- Serial/batch policy must be resolved for serial/batch items.
- Location and warehouse scope policy must be resolved.
- Evidence reference and manager event must exist.
- Inventory/Admin approval reference must exist.
- Idempotency request id must exist.
- Source payload hash must be stable.
- Draft creation must return false stock-posting flags.

Draft eligibility must be deny-by-default. Missing evidence, unresolved policy, unexpected fields, invalid warehouse context, or native-route requirements must block draft creation.

## 6. Exclusion Rules

The following must exclude a line or request from any future Stock Reconciliation draft:

- Draft, in-progress, submitted-for-review, or recount-requested source task.
- Request-only handoff without Inventory/Admin approval.
- Source warehouse not visible.
- Line warehouse mismatch.
- Missing item identity.
- Counted quantity is invalid or inconsistent.
- Variance quantity is missing where required.
- Variance direction does not match variance quantity.
- Zero count unresolved.
- Missing item unresolved.
- Unexpected item unresolved.
- Quarantine or damaged posture unresolved.
- Blocked line unresolved.
- Serial number requirement unresolved.
- Batch requirement unresolved.
- Location restriction unresolved.
- Native route link required to proceed.
- Valuation, accounting, commercial, rate, amount, tax, GL, cost, margin, profit, debit, credit, payable, payment, billing, landed cost, or price fields required to proceed.
- Client supplies arbitrary Stock Reconciliation rows instead of server-derived lines.
- Request id reused with changed payload.
- Request id reused across another handoff request.

Excluded quantities must not be silently drafted. They must remain in custom evidence/status records for Inventory/Admin review.

## 7. Draft Behavior If Later Approved

If a later phase approves Stock Reconciliation draft creation, that phase must still be limited to an unsubmitted draft.

Allowed only after later approval:

- Prepare one unsubmitted Stock Reconciliation draft for Inventory/Admin review.
- Use server-derived rows from the approved custom handoff request.
- Preserve warehouse, item, UOM, counted quantity, variance posture, and evidence references.
- Store safe custom reference text back to custom request records.
- Return safe status flags showing no stock posted.

Still blocked even in a draft phase unless separately approved:

- Stock Reconciliation submit.
- Stock Reconciliation cancel.
- Stock Reconciliation amend.
- Stock Reconciliation delete.
- Stock posting.
- Any stock posting from Warehouse Console.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Entry creation or submission.
- Stock Reservation.
- Reserve/unreserve.
- Native route exposure to Warehouse users.
- Valuation/accounting/commercial payload exposure.
- Background jobs that submit, post, reconcile, or mutate stock.

The future draft method must not call submit, cancel, amend, delete, enqueue-post, reserve, unreserve, or stock-posting routines.

## 8. Native Submit Bypass Containment

Native-submit bypass containment is mandatory before any runtime draft phase.

Owner/security must decide:

- Who can open a generated Stock Reconciliation draft in native ERPNext.
- Whether Warehouse users can see only a plain text draft reference.
- Whether Stock Manager can open a native draft or only Inventory/Admin can.
- Whether draft submit is technically blocked for Warehouse roles.
- Whether native submit requires a separate Inventory/Admin role.
- Whether draft references are never clickable in Warehouse UI.
- Whether generated drafts carry custom metadata or naming policy.
- Whether native form permissions prevent accidental submit/cancel/amend.
- Whether post-submit status can be reflected back to Warehouse as read-only text.

Default recommendation:

- Warehouse sees plain text/status only.
- Warehouse does not receive native Stock Reconciliation links.
- Inventory/Admin owns native draft access.
- Submit remains outside Warehouse Console.

## 9. Role Ownership

Warehouse ownership:

- Physical count evidence.
- Count and variance posture.
- Manager recommendation.
- Request-only handoff.

Inventory/Admin ownership:

- Stock adjustment policy.
- Tolerance policy.
- Location and warehouse policy.
- Serial/batch policy.
- Native-submit containment.
- Future Stock Reconciliation draft governance.
- Future Stock Reconciliation submit governance.

System/Admin ownership:

- Permission model.
- Native form containment.
- Protected gates.
- Audit and rollback policy.

Finance/Admin ownership:

- Accounting impact policy if a variance has financial consequence.
- Write-off or value adjustment governance if separately approved.
- GL/accounting review outside Warehouse payloads.

Sales and Procurement ownership:

- No normal ownership in cycle count Stock Reconciliation draft policy.
- Sales is involved only if a variance affects customer promise, dispatch commitment, or customer-facing resolution.
- Procurement is involved only if a variance relates to supplier dispute, supplier return, or receiving correction.

## 10. Reference Visibility Policy

Until native route containment is approved, all references shown in Warehouse UI must be inert text/status only.

Allowed:

- Plain text request id.
- Plain text future draft reference if later approved.
- Safe status text.
- Safe policy state.
- Safe Inventory/Admin review reference.

Blocked:

- `Link` fields to Stock Reconciliation.
- `Dynamic Link` fields to Stock Reconciliation.
- Native route URL.
- HTML link.
- Button that opens native form.
- `/app`
- `/desk/Form`
- `/desk/List`
- `/desk/Report`
- `/desk/query-report`
- File or attachment field unless later security review approves attachment policy.

## 11. Audit And Idempotency

Any future draft phase must preserve:

- Source custom handoff request id.
- Source cycle count task id.
- Manager decision status.
- Inventory/Admin approval reference.
- Source payload hash.
- Request id.
- Draft request id.
- Requesting user.
- Timestamp.
- Derived line list.
- Excluded line list.
- Event log.
- No-effect flags.

Idempotency rules:

- Same request id plus same payload returns the existing draft/request.
- Same request id plus changed payload rejects.
- Same request id reused across another handoff rejects.
- Source payload hash mismatch rejects.
- Post-submit or cancelled native document must not be overwritten from Warehouse Console.

## 12. Future Test Requirements

Any future Stock Reconciliation draft runtime phase must include tests proving:

- Warehouse User cannot create Stock Reconciliation draft.
- Stock User cannot create Stock Reconciliation draft unless owner explicitly approves.
- Warehouse Manager cannot submit Stock Reconciliation.
- Draft creation requires Inventory/Admin approval reference.
- Draft creation requires approved custom handoff request.
- Draft creation rejects unreviewed cycle count tasks.
- Draft creation rejects request-only handoff without approval.
- Draft creation rejects source status mismatch.
- Draft creation rejects native route requirement.
- Draft creation rejects arbitrary client-supplied Stock Reconciliation rows.
- Draft creation rejects valuation/accounting/commercial fields in Warehouse payload.
- Draft creation rejects notification/email/portal behavior.
- Draft creation is idempotent.
- Changed payload with same request id rejects.
- Cross-handoff request id reuse rejects.
- Response flags show no stock posted.
- Stock Reconciliation is not submitted.
- Stock Ledger is not mutated.
- Stock Balance is not mutated.
- Stock Entry is not created.
- Stock Reservation is not created.
- Sales runtime is unchanged.
- Procurement runtime is unchanged.

## 13. Owner Decisions Before Runtime

Before any W15H Stock Reconciliation draft runtime phase, owners must decide:

- Whether Stock Reconciliation draft creation is allowed at all from Warehouse Console.
- Which role owns draft preparation.
- Whether Stock Manager may prepare drafts or only Inventory/Admin/System Manager.
- Whether Warehouse users ever see draft references.
- Whether draft references are plain text only.
- Whether native Stock Reconciliation route access is allowed for any Warehouse role.
- Whether native submit is technically blocked for Warehouse roles.
- Which handoff types can create a draft.
- Which source statuses can create a draft.
- Which variance directions are eligible.
- Which count scopes are eligible.
- Which warehouses are eligible.
- Whether serial/batch items are included.
- Whether zero count, missing item, unexpected item, quarantine, and blocked lines are excluded or separately reviewed.
- Whether valuation/accounting fields remain hidden from Warehouse.
- Whether Finance/Admin approval is required for value-impacting adjustments.
- Whether attachments/photos are allowed later.
- What rollback/cancel/amend policy applies after native document creation.
- What post-submit read-only status, if any, may return to Warehouse.

## 14. Recommendation

Recommendation: do not implement Stock Reconciliation draft runtime yet.

The correct next state after W15H8 is this W15H9 policy gate. If owner/security later approve a draft phase, implement it as a separate Inventory/Admin-owned runtime phase with strict server-side eligibility, no native route exposure for Warehouse users, no submit/post behavior, no valuation/accounting/commercial payload exposure, and deny-by-default tests.

Until that separate approval exists, W15H remains complete at custom evidence, manager posture, request-only Inventory/Admin handoff, and Stock Reconciliation draft policy documentation.
