# Warehouse Console Phase W11B Purchase Receipt Receiving Execution Design

Date: 2026-05-31

Branch: `feature/erpnext-ui-design`

Status: docs-only Warehouse Agent design package. This document does not implement runtime code, routes, backend methods, tests, smokes, hooks, fixtures, live alignment, Purchase Receipt creation, Purchase Receipt submission, Stock Entry behavior, Delivery Note behavior, Stock Reservation behavior, Stock Reconciliation behavior, serial/batch behavior, barcode behavior, native ERP access, Warehouse Quick Find/Search, Sales runtime behavior, or Procurement runtime behavior.

## 1. Acceptance Decision

Decision: `design_only_implementable_later_after_reviews`.

W11B should be accepted as a design package only. It is not an implementation approval.

The future receiving workflow is a valid candidate for a separately governed execution track because it is adjacent to the protected Inbound Receiving queue and Receiving Review page. It is not safe to implement directly from this document. Purchase Receipt submit/cancel in installed ERPNext source updates previous documents, stock ledger, and GL paths, and may interact with quality inspection, reservation, serial/batch, rejected warehouse, and billing state. Security/Stability Review Agent and Operation Reviewer Agent must review this design before Main Control can ask the owner for any runtime approval.

Recommended implementation posture if later approved:

1. First runtime candidate: manager-only receiving execution preparation and draft Purchase Receipt creation, with no auto-submit.
2. Separate later candidate: manager-only Purchase Receipt submission after Security/Stability and Operations approve stock posting guardrails.
3. No Warehouse User execution in the first candidate.

## 2. Sources Reviewed

Project sources:

- `_docs/erp-ui-customization/warehouse-console-phase-w11a-execution-readiness-synthesis-2026-05-31.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w11-execution-readiness-boundary-plan-2026-05-31.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w10b-read-only-freeze-closure-2026-05-31.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w10c-page-chrome-fix-2026-05-31.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w4b-receiving-review-baseline-2026-05-28.md`
- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`

Installed ERPNext source in `erpai_project1-backend-1`:

- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/purchase_receipt/purchase_receipt.py`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/purchase_receipt/purchase_receipt.json`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/purchase_receipt_item/purchase_receipt_item.json`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.json`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/purchase_order_item/purchase_order_item.json`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/quality_inspection/quality_inspection.json`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/item/item.json`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/serial_and_batch_bundle/serial_and_batch_bundle.py`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/stock_reservation_entry/stock_reservation_entry.py`

Official ERPNext references:

- Purchase Receipt: https://docs.frappe.io/erpnext/purchase-receipt
- Stock Entry: https://docs.frappe.io/erpnext/stock-entry
- Stock Reconciliation: https://docs.frappe.io/erpnext/stock-reconciliation
- Stock Reservation: https://docs.frappe.io/erpnext/stock-reservation
- Serial and Batch Bundle: https://docs.frappe.io/erpnext/serial-and-batch-bundle

## 3. Findings By Severity

Critical: Purchase Receipt submit is stock/accounting execution.

Evidence: installed `purchase_receipt.py` calls `update_prevdoc_status`, `update_billing_status`, `update_stock_ledger`, and `make_gl_entries` in `on_submit`; cancel paths call `update_stock_ledger` and `make_gl_entries_on_cancel`. This means a custom Warehouse submit action is not a UI-only operation. It posts stock and can affect financial/accounting state through ERPNext stock controller behavior.

Critical: client payload must never carry valuation or commercial fields.

Evidence: Purchase Receipt Item includes `rate`, `amount`, `valuation_rate`, `allow_zero_valuation_rate`, and related stock fields. The future Warehouse write contract must derive all ERPNext-required commercial/valuation fields server-side or leave ERPNext defaults intact. Warehouse payloads must not expose or accept rate, amount, valuation, tax, landed cost, billing, payment, or supplier pricing fields.

High: quality inspection and rejected quantity must not be treated as ordinary receipt lines.

Evidence: current read-only W4B Receiving Review intentionally excludes Quality Inspection creation/approval/rejection. Purchase Receipt Item includes `quality_inspection`, `rejected_qty`, and `rejected_warehouse`. Item includes `inspection_required_before_purchase`. A future receiving design must block or route quality-required and rejected-quantity cases unless those flows are explicitly designed.

High: serial/batch items require a separate controlled design.

Evidence: Purchase Receipt Item exposes serial and batch fields and Serial and Batch Bundle links. Serial and Batch Bundle source validates serial/batch availability, voucher status, future entries, and inventory. W11B must not authorize serial/batch assignment or bundle creation.

High: idempotency and stale-state controls are mandatory.

Evidence: Purchase Orders can become fully or partly received between page render and action. Duplicate clicks can create duplicate draft receipts or attempt duplicate stock posting. The write contract must use idempotency keys, source document modified/version checks, and line-level remaining quantity revalidation inside the transaction.

High: draft-only execution still needs native-submit containment and draft ownership rules.

Evidence: a draft Purchase Receipt is still a real ERPNext document. If a future draft-phase actor, Stock Manager, System Manager, or another operational role can submit that draft through native ERPNext before the custom submit phase is approved, the staged safety model is bypassed. A future draft-only phase must prove that normal Warehouse actors cannot natively submit generated drafts, must define who owns prepared drafts, and must define how duplicate, abandoned, or stale drafts are resumed, expired, or closed without confusing receiving users.

Medium: current read-only Receiving Review is a good launch context, but should stay visibly read-only.

Evidence: W4B route `/desk/warehouse-console-receiving/<purchase-order>` is protected and read-only. It already shows supplier, target warehouse, receiving state, item lines, and receipt history. Execution mode must be visually and technically separate so the frozen read-only visibility baseline remains stable.

Medium: Purchase and Finance boundaries are adjacent.

Evidence: Procurement owns PO commercial sourcing and pricing. Finance owns billing/accounting. Purchase Receipt touches PO receiving state and can influence billing status/accounting paths. Warehouse execution must not mutate PO commercial terms, supplier prices, Item Price, Default Supplier, Item Supplier, invoices, payments, or accounting configuration.

## 4. Scope For Future Receiving Design

Future candidate workflow: controlled Purchase Receipt receiving from one submitted Purchase Order already visible in Warehouse Receiving Review.

In scope for design only:

- Manager-only review of a submitted open Purchase Order.
- Selection of eligible open PO item lines.
- Accepted quantity entry up to remaining open quantity.
- Server-side Purchase Receipt draft creation in a future implementation, if approved.
- Separate future submit design for stock posting, if approved after additional review.
- Structured audit record for every future write attempt.
- Custom Warehouse shell success, conflict, restricted, unavailable, and error states.

First future implementation candidate should be draft-only unless Main Control and owner explicitly approve submission. Draft creation is still a mutation, but it does not post stock ledger. Submission is a separate stock execution milestone.

## 5. Non-Scope And Forbidden Boundary

Forbidden until a later owner-approved implementation phase:

- Purchase Receipt creation, submission, cancellation, amendment, close, reopen, or posting in the current read-only baseline.
- Stock Entry, Delivery Note, Pick List, Stock Reservation, Stock Reconciliation, Serial and Batch Bundle, barcode, workflow, email, print, portal, AI, or background job behavior.
- Quality Inspection creation, approval, rejection, or mutation.
- Serial number assignment, batch assignment, Serial and Batch Bundle creation, or rejected serial/batch handling.
- Over-receipt tolerance override.
- Rejected quantity receiving unless rejected warehouse handling is separately approved.
- PO commercial mutation: supplier, item, price, rate, tax, payment terms, Item Price, Default Supplier, Item Supplier.
- Purchase Invoice, payment, GL, landed cost, stock valuation, stock value, valuation rate, amount, rate, cost, margin, profit, billing, or accounting exposure.
- Native ERP Form/List/Report/Workspace escape.
- Warehouse Quick Find/Search.
- Sales runtime changes.
- Procurement runtime changes.

## 6. Role Gates And Actor Model

Initial execution actor model:

- Warehouse Manager: candidate execution actor for future draft creation only, after owner approval.
- Stock Manager: candidate execution actor only if the owner confirms this role maps to Warehouse Manager for this site.
- Warehouse User / Stock User: read-only in the first execution track. May review receiving posture but must not create or submit Purchase Receipts.
- System Manager: support visibility only; not a normal receiving actor inside the custom Warehouse UI.
- Purchase Manager / Purchase User: no Warehouse execution access unless they also have an approved Warehouse execution role. Procurement remains PO commercial owner.
- Finance / Accounts User: no Warehouse execution access. Finance owns billing/accounting review outside Warehouse.

Required future gates:

1. Authenticated user.
2. Custom Warehouse execution role gate, initially manager-only.
3. ERPNext DocPerm read on Purchase Order.
4. ERPNext DocPerm create/write on Purchase Receipt for draft creation.
5. ERPNext DocPerm submit on Purchase Receipt only if a separate submit phase is approved.
6. No broad native Desk/admin bypass for normal Warehouse actors.
7. Server-side recheck on every request; no trust in client-side role state.
8. Server-derived actor proof from the active session on every request; client-supplied user, role, or permission claims are ignored.
9. CSRF/session protection for every future write request, plus a confirmation token bound to actor, source Purchase Order, action type, payload hash, and expiry.
10. Draft-only phases must prove that approved draft creators cannot submit Purchase Receipts through native ERPNext or any other unapproved route unless the separate submit phase is explicitly approved.

## 7. Eligible Source Documents

Eligible Purchase Order parent:

- `docstatus = 1`.
- `status` is receiving-open, such as `To Receive` or `To Receive and Bill`.
- `per_received < 100`.
- Not `Draft`, `Cancelled`, `Closed`, `Completed`, `On Hold`, or otherwise blocked by ERPNext validation.
- Company is readable and consistent with the future Purchase Receipt company.
- Supplier is present and matches the source Purchase Order.
- Purchase Order is readable by the actor.
- Purchase Order has at least one eligible line with remaining quantity.

First execution track should exclude:

- Subcontracted Purchase Orders.
- Internal supplier/from-warehouse Purchase Orders.
- Return flows.
- Inter-company or special purchase flows that require supplier warehouse or from warehouse behavior.
- POs with mixed companies or company/warehouse mismatch.
- POs already fully received by the time the server validates.

Eligible Purchase Order Item line:

- Child line belongs to the selected submitted Purchase Order.
- `item_code` is present.
- Remaining quantity is greater than zero: `qty - received_qty > 0` using server-side precision.
- Target warehouse is present on line or resolvable from parent `set_warehouse`.
- UOM and conversion factor are present and valid.
- Item is not blocked by serial/batch or quality constraints unless those constraints are separately handled.
- Line is not already fully received.

## 8. Line Rules And Constraint Handling

Partial receipt behavior:

- Allowed in design: accepted quantity can be less than remaining quantity.
- Server recomputes remaining quantity from latest Purchase Order state.
- UI should show both ordered, already arrived, and still open quantities.
- Success state must clarify that open quantities may remain.

Over-receipt behavior:

- Forbidden in first execution design.
- Accepted quantity must be `0 < accepted_qty <= remaining_qty` after server revalidation.
- Any over-receipt tolerance, supplier overage, or business override must remain native ERPNext or require a separate owner-approved design.

Warehouse mismatch behavior:

- Future UI may show target warehouse but must not let the actor freely choose arbitrary warehouses in v1.
- Default accepted warehouse must come from PO Item `warehouse` or parent `set_warehouse`.
- If no warehouse is available, line is ineligible.
- If a proposed warehouse differs from source line warehouse, block and return `warehouse_mismatch` unless a later transfer/putaway design exists.

UOM behavior:

- UI may display PO UOM and Stock UOM.
- Actor quantity should be entered in the same operational UOM shown on the PO line.
- Server must recompute stock quantity from ERPNext conversion factor.
- Client must not send or mutate conversion factor.
- Fractional quantities must respect ERPNext UOM integer rules.

Rejected warehouse behavior:

- First execution design should set rejected quantity to zero and not expose rejected receiving.
- If rejected receiving is later approved, every rejected quantity requires a rejected warehouse and separate copy that does not imply accepted stock.
- Rejected quantity should not be hidden inside accepted quantity.

Quality inspection behavior:

- If Item or source flow requires inspection before purchase, block v1 receiving execution and show `Quality inspection required` unless a linked submitted/accepted Quality Inspection is already available and approved for this flow.
- W11B does not authorize Quality Inspection creation, approval, rejection, or mutation.
- Quality-required lines should remain read-only in v1 or be routed to a future Quality design track.

Serial/batch behavior:

- If Item has serial or batch control, block v1 receiving execution and show `Serial or batch details required`.
- W11B does not authorize serial/batch capture, Serial and Batch Bundle creation, batch creation, or serial number assignment.
- A later serial/batch design must include scanning/manual entry validation, duplicate checks, warehouse checks, voucher-detail checks, and rollback behavior.

Unavailable data states:

- `restricted`: actor lacks Warehouse execution role or ERPNext DocPerm.
- `ineligible`: PO or line is not open for receiving.
- `stale`: PO modified or received quantity changed after page render.
- `conflict`: idempotency key maps to a different payload or a duplicate in-progress attempt exists.
- `quality_required`: quality inspection constraint blocks line.
- `serial_batch_required`: serial/batch constraint blocks line.
- `warehouse_missing`: no target warehouse is available.
- `warehouse_mismatch`: proposed warehouse differs from eligible source warehouse.
- `over_receipt_blocked`: quantity exceeds latest remaining quantity.
- `server_error`: business-safe failure copy with no raw framework traceback.

## 9. Future Backend Write Contract Design

No backend methods are implemented in W11B. The following names are design placeholders only.

Future read/preview method:

- `get_warehouse_receiving_execution_context(purchase_order)`
- Purpose: return latest eligibility, line constraints, default warehouses, and an execution token for manager-only future UI.
- Must not create or mutate records.

Future draft creation method:

- `create_warehouse_purchase_receipt_draft(payload)`
- Purpose: create one draft Purchase Receipt from one eligible submitted Purchase Order.
- Must require idempotency key.
- Must require manager-only Warehouse execution role.
- Must reject valuation, rate, amount, tax, billing, payment, supplier pricing, and native route fields in payload.
- Must enforce write-attempt rate limiting keyed by actor, source Purchase Order, and action type.
- Must reject expired, replayed, or mismatched confirmation tokens before creating any draft.
- Must prevent native-submit bypass for generated drafts during a draft-only phase, either through role permission design, workflow state design, or another Security/Stability-approved control.
- Must return an existing matching prepared draft for an idempotent replay instead of creating another draft.

Future submit method, separate phase only:

- `submit_warehouse_purchase_receipt(receipt_name, idempotency_key, expected_receipt_modified)`
- Purpose: submit a previously created eligible draft Purchase Receipt.
- Must be separately approved because submit triggers stock ledger and GL behavior.

Required draft creation inputs:

- `purchase_order`.
- `source_po_modified` or source revision marker.
- `idempotency_key` generated before confirmation.
- `confirmation_token` bound to visible confirmation copy, actor, source Purchase Order, payload hash, and short expiry.
- `lines`: list of `{purchase_order_item, item_code, accepted_qty, warehouse}`.
- Optional `client_observed_remaining_qty` for stale-state diagnostics only, never as authority.

Rejected from input:

- `rate`, `amount`, `valuation_rate`, `stock_value`, `tax`, `landed_cost`, `payment`, `billing`, `supplier_price`, `item_price`, `gl_account`, `expense_account`, `cost_center`, `serial_no`, `batch_no`, `serial_and_batch_bundle`, native route strings, submit/cancel/amend flags.

Validation order:

1. Authenticate user.
2. Validate custom Warehouse manager execution role.
3. Validate ERPNext DocPerm on Purchase Order and Purchase Receipt.
4. Parse and validate idempotency key.
5. Validate the session-bound confirmation token, expiry, actor, source Purchase Order, action type, and payload hash.
6. Apply write-attempt rate limiting before any document mutation.
7. Load source Purchase Order in a transaction and verify latest modified/state.
8. Verify parent eligibility: submitted, open, not closed/cancelled/on hold, receiving remaining.
9. Load source lines from parent document or controlled child read.
10. Validate every requested line belongs to the PO and remains open.
11. Validate quantities, UOM, target warehouse, company, supplier, quality, serial/batch, and rejected quantity constraints.
12. Reject any payload field outside the allowlist.
13. Create an audit attempt record with `pending` state.
14. Create the draft Purchase Receipt using ERPNext document APIs in the same transaction.
15. Re-read resulting draft state and store audit success with generated receipt name.
16. Return custom Warehouse success payload with no native route target.
17. On error, rollback draft creation and store a business-safe failure audit after rollback.

Draft lifecycle rules:

- A prepared draft must have a clear owner-facing state such as `Draft receipt prepared - stock not posted`.
- A future design must define whether prepared drafts can be resumed, refreshed, abandoned, expired, or closed.
- Reopening the same PO and same selected quantities should show the existing matching prepared draft rather than creating another one.
- If the source PO changed after draft creation, the custom UI must force refresh and explain that the draft may no longer match current receiving posture.
- Draft cleanup must not delete or cancel ERP documents silently; any cleanup behavior needs explicit owner and Security/Stability approval.

Transaction boundary:

- Draft creation must be all-or-nothing.
- If any line fails, no Purchase Receipt draft should be created unless a later partial-success design explicitly exists.
- Submission must be a separate transaction and must not reuse stale draft data.
- Failure audit needs to survive rollback. Use a post-rollback audit write or a separate safe logging mechanism approved by Security/Stability.

Idempotency behavior:

- Every write attempt requires a unique idempotency key scoped to actor, PO, action type, and payload hash.
- Repeating the same key and same payload returns the previous result.
- Repeating the same key with a different payload returns `conflict`.
- In-progress duplicate attempts return `in_progress` and do not create another draft.
- Expired confirmation tokens require refresh and cannot be replayed.
- Repeated denied, conflict, or invalid attempts should be throttled and audited without exposing whether a hidden Purchase Order exists.
- Client-side duplicate-click protection is required but never sufficient without server idempotency.

Structured errors:

- `restricted`
- `ineligible_source`
- `stale_source`
- `invalid_quantity`
- `over_receipt_blocked`
- `warehouse_missing`
- `warehouse_mismatch`
- `quality_required`
- `serial_batch_required`
- `permission_denied`
- `idempotency_conflict`
- `draft_create_failed`
- `submit_not_approved`

## 10. Future UI Mode Separation

Current read-only route remains unchanged:

- `/desk/warehouse-console-receiving/<purchase-order>`

Design rule:

- The current Receiving Review route stays read-only by default.
- No disabled fake execution button should appear in the frozen read-only surface.
- Any future execution entry must be hidden unless the user has the approved manager execution role.
- Execution mode must have a visibly distinct header, confirmation panel, and audit summary so users understand they are leaving review and entering a write workflow.

Possible future execution surface, design only:

- A manager-only execution panel within Receiving Review after explicit approval; or
- A separate custom route such as `/desk/warehouse-console-receiving-execution/<purchase-order>` if Hardening recommends route isolation.

Preferred first design: route isolation. It reduces accidental execution drift in the frozen read-only page and gives smokes a clear shell to protect.

Allowed future controls after approval only:

- `Back to receiving review`.
- `Refresh receiving state`.
- `Prepare draft receipt`.
- `Confirm draft receipt`.

Submit controls are not part of the first implementation candidate unless a separate submit phase is approved.

Confirmation copy requirements:

- State that a Purchase Receipt draft will be created.
- Show supplier, PO, selected lines, accepted quantities, warehouses, and quality/serial constraints.
- Say that no stock is posted until a submitted receipt phase exists, if the first phase is draft-only.
- Never use native ERP wording or route links.

Success state:

- Show custom Warehouse confirmation with receipt id as text.
- State clearly that this is a prepared draft only and that stock has not been posted.
- If an existing matching draft is reused, say `Existing draft receipt found` instead of implying a new receipt was created.
- Do not route to native Purchase Receipt form.
- Offer only custom Warehouse navigation, such as back to Receiving Review or Inbound Receiving.

Failure state:

- Keep the user in the custom Warehouse shell.
- Show safe business copy and a retry/refresh path.
- Do not expose tracebacks, SQL, DocType internals, or native links.

## 11. Audit Evidence Model

A future implementation needs an app-owned audit record before runtime approval. Suggested design name: `Warehouse Receiving Execution Audit` or equivalent. This is not created in W11B.

Required audit fields:

- Audit id.
- Actor user.
- Actor roles at the time of attempt.
- Timestamp.
- Action type: preview, draft_create, submit.
- Source Purchase Order.
- Source Purchase Order modified/version marker.
- Source supplier.
- Source company.
- Idempotency key.
- Payload hash.
- Selected Purchase Order Item ids.
- Item codes.
- Accepted quantities.
- Rejected quantities, if ever approved.
- Warehouses.
- Before status and before percent received.
- After status and after percent received, if write succeeds.
- Resulting Purchase Receipt id, if created.
- Resulting Purchase Receipt status/docstatus.
- Draft lifecycle state, such as prepared, reused, stale, abandoned, submitted by approved later flow, or blocked.
- Failure reason code.
- Human-safe failure detail.
- Correlation/request id.

Audit rules:

- Do not store valuation, rate, amount, tax, margin, profit, landed cost, billing, payment, or supplier price data.
- Do not store raw tracebacks as user-visible audit detail.
- Audit must distinguish draft creation from stock-posting submission.
- Audit must record duplicate/idempotent replay outcomes.

## 12. Test, Smoke, Static Scan, And Gate Standard

Before any runtime implementation:

- Security/Stability approval of write contract.
- Operation Reviewer approval of business flow and copy.
- Main Control owner approval.
- Test plan accepted before code.

Required future unit/contract tests:

- Manager role can access execution context.
- Warehouse User cannot create or submit.
- Purchase Manager/Sales/Finance cannot execute unless approved Warehouse role is also present.
- Missing ERPNext DocPerm returns restricted state.
- Draft PO, cancelled PO, closed PO, completed PO, on-hold PO, and fully received PO are blocked.
- Line not belonging to PO is blocked.
- Zero, negative, fractional-invalid, and over-remaining quantities are blocked.
- Warehouse missing/mismatch is blocked.
- Quality-required lines are blocked unless accepted Quality Inspection support is approved.
- Serial/batch items are blocked unless serial/batch support is approved.
- Payload with valuation, rate, amount, tax, GL, account, payment, billing, native route, submit/cancel/amend fields is rejected.
- Duplicate idempotency key same payload returns same result.
- Duplicate idempotency key different payload returns conflict.
- Existing matching prepared draft is reused or surfaced instead of creating another draft.
- Draft-phase actors cannot submit generated Purchase Receipts through native ERPNext when submit phase is not approved.
- Stale source modified/received quantities return stale state.
- Failure path leaves no draft receipt unless explicitly recorded as success.

Required future Playwright smoke coverage:

- Manager-only execution entry visibility.
- Warehouse User read-only behavior remains unchanged.
- Receiving Review remains read-only for non-execution actors.
- Execution route/panel loads in one custom Warehouse shell.
- Confirmation panel lists selected lines and quantities.
- Duplicate click does not create duplicate result.
- Stale-state fixture returns business-safe conflict.
- No native Purchase Receipt form/list/report link appears.
- No valuation/accounting/commercial text appears.
- No Stock Ledger or Stock Balance link appears.
- Browser refresh/back/repeated navigation keeps one shell.
- Sales freeze passes.
- Procurement protected gate passes.
- Full protected workspace gate passes before commit and after live alignment.

Required static scans:

- Native route escape terms.
- Lifecycle/control labels outside approved execution route.
- Valuation/accounting/commercial field names.
- Server write calls limited to approved receiving service methods.
- No writes in read-only Warehouse methods.
- No Sales runtime dirty files.
- No Procurement runtime dirty files.
- No smoke/test weakening.

Source/live evidence before any live alignment:

- Source unit tests.
- Source focused receiving execution smoke.
- Sales freeze.
- Procurement protected gate.
- Full protected workspace source gate.
- Commit and push by Main Control only.
- Live-align approved runtime files only.
- Source/live SHA-256 hash proof.
- Focused live receiving execution smoke.
- Final protected live gate.

## 13. Sales And Procurement Boundary Protection

Procurement boundary:

- Procurement owns sourcing, supplier selection, RFQ, Supplier Quotation, Purchase Order commercial ownership, supplier pricing, Item Price, Default Supplier, and Item Supplier mutation.
- Warehouse may only act on an already submitted Purchase Order that is receiving-open.
- Warehouse must not edit PO header, supplier, prices, taxes, terms, items, or procurement readiness data.
- Warehouse receiving execution cannot create or amend Purchase Orders.

Sales boundary:

- Sales Console must not change.
- Delivery Note, customer shipment, picking completion, reservation for sales demand, and customer-facing fulfillment remain outside W11B.
- No Sales Order mutation.

Finance boundary:

- Purchase Invoice, billing, payment, GL, landed cost, valuation, tax, and accounting remain outside Warehouse.
- Accounts User visibility does not imply Warehouse execution rights.

Shared runtime boundary:

- Any future implementation touching shared registry/sidebar/boot/runtime must rerun Sales freeze and full protected workspace gates.
- Execution design should prefer Warehouse-owned modules and routes to avoid weakening Sales or Procurement.

## 14. Recommended Phase Split If Owner Later Approves

R0: Docs-only receiving design review.

- Current W11B output.
- Security/Stability and Operation Reviewer review.
- Owner decision.

R1: Premium receiving UI polish, no writes.

- Improve Receiving Review readability and line selection affordance without execution.
- Confirm owner visual acceptance.

R2: Manager-only execution context preview, no writes.

- Custom route or panel showing eligibility and constraints.
- No Purchase Receipt creation.

R3: Manager-only Purchase Receipt draft creation.

- Create draft Purchase Receipt from eligible PO lines.
- No submit.
- Strong idempotency and audit.

R4: Purchase Receipt submission design.

- Separate Security/Stability and Operations approval.
- Stock ledger and GL side effects explicitly reviewed.

R5: Serial/batch, quality, rejected quantity, and scanning extensions.

- Separate designs only after base receiving is stable.

## 15. Open Owner Decisions

1. Should the first execution candidate create draft Purchase Receipts only, or should submit ever be in the same release?
2. Should only Warehouse Manager execute, or should Stock Manager also be accepted as equivalent?
3. Should Warehouse User remain read-only permanently for receiving execution?
4. Are serial/batch-controlled items excluded from v1 execution?
5. Are quality-inspection-required items excluded from v1 execution unless an accepted inspection already exists?
6. Are rejected quantities excluded from v1 execution?
7. Should execution use a separate custom route for stronger freeze protection?
8. What audit record name and retention policy should be used?
9. How should native Purchase Receipt submit bypass be prevented during a draft-only phase?
10. Who owns prepared drafts, and what is the approved abandoned/stale draft policy?
11. Should owner manual Premium UI review happen before or after Security/Stability design review?

## 16. Main Control Review Synthesis

Security/Stability Review Agent accepted W11B with docs fixes. The accepted hardening adds explicit requirements for server-derived actor proof, CSRF/session binding, confirmation token expiry, replay rejection, write-attempt rate limiting, and audited denied or invalid attempts.

Operation Reviewer Agent accepted W11B with docs fixes. The accepted operational hardening clarifies that draft Purchase Receipt creation is still a mutation, generated drafts must not be submit-able through native ERPNext by normal Warehouse actors before a submit phase is approved, prepared draft ownership must be explicit, stale draft handling must be defined, abandonment/expiry must be policy-driven, and silent cleanup is not acceptable.

Main Control accepts W11B as a docs-only design package only. This is not runtime approval. Purchase Receipt draft creation, Purchase Receipt submission, stock posting, native ERP route access, valuation/accounting exposure, Quick Find/Search, Sales runtime changes, and Procurement runtime changes remain blocked.

The next safe choices are:

1. Keep execution deferred and continue normal owner review.
2. Start premium receiving UI polish as a read-only phase, with no disabled execution buttons and no write surface.
3. Create another docs-only checkpoint for owner decisions and native-submit containment, without runtime implementation.

Do not send a runtime implementation prompt yet.

## 17. Recommendation

W11B should remain design-only through Security/Stability and Operation Reviewer validation.

Implementation is not blocked by lack of business value. It is blocked by the need for explicit write-safety standards, audit design, idempotency, stale-state behavior, draft ownership, native-submit containment, serial/batch and quality constraints, premium UI walkthrough, and owner approval.

Recommended next task after this docs-only package is committed:

- Main Control should ask the owner whether to continue with premium receiving UI polish, keep execution deferred, or authorize another docs-only design checkpoint.

Do not send a runtime implementation prompt yet.

## 18. Validation

Validation to be completed by Warehouse Agent after this docs-only file is created:

- `git status --short --branch`
- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
