# Warehouse Console Phase W14D Inbound Arrival Readiness Design

Date: 2026-06-16

Status: `superseded_by_w15a_operations_blueprint`

Superseded by:

- `warehouse-console-phase-w15a-operations-blueprint-2026-06-16.md`

Use this W14D document as historical inbound-readiness input only. The active Warehouse operations roadmap after Phase 0 is W15A-W15J, and inbound receiving is now planned as W15C.

Decision: `design_only_ready_for_owner_review`

Scope: docs-only design for the first real Warehouse operations workflow after Phase 0. This document does not implement runtime, backend methods, routes, smokes, live alignment, Purchase Receipt creation, Purchase Receipt submission, stock posting, supplier messaging, native ERP access, Sales runtime behavior, or Procurement runtime behavior.

## 1. Purpose

Phase 0 moved Warehouse Quick Find into the shared sidebar Search helper and removed the duplicated Manager Readiness component from the Overview page.

W14D defines how inbound arrival work should become operationally useful without jumping directly into stock mutation. The goal is to give warehouse users and warehouse managers a clear arrival-readiness workflow tied to Purchase Orders while preserving Procurement ownership of supplier/PO decisions and ERPNext ownership of Purchase Receipt posting.

## 2. Daily Business Flow

Use this plain-language flow for owner and operations review.

1. Procurement approves or maintains a Purchase Order.
2. The Warehouse Console automatically shows the Purchase Order in Inbound Receiving when stock is still expected.
3. Warehouse users wait for the supplier delivery and review what is due, overdue, partially arrived, or expected soon.
4. When goods physically arrive, Warehouse users compare the arrival against the PO lines.
5. If everything is clear, Warehouse can mark the arrival as ready for manager review in a future non-mutating readiness phase.
6. If there is an issue, Warehouse records or flags the issue in a future controlled readiness phase: shortage, overage, damage, wrong item, missing warehouse, quality check needed, or unclear supplier paperwork.
7. Warehouse Manager reviews the arrival readiness and decides the next path:
   - ready for Purchase Receipt preparation later;
   - needs Procurement follow-up;
   - needs warehouse correction;
   - needs quality/damage review;
   - not enough visible detail.
8. Purchase Receipt creation and submission remain a separate future governed write phase. W14D does not approve them.

## 3. Page Strategy

Do not add a separate top-level page for inbound actions yet.

Use the existing pages:

- Inbound Receiving Queue: planning board for all expected supplier arrivals.
- Receiving Review: object page for one Purchase Order.

Recommended future UI placement:

- Inbound Receiving Queue stays mostly review/navigation.
- Receiving Review becomes the primary place for arrival readiness and discrepancy review because it has the PO context, supplier, target warehouse, line quantities, and receipt history.
- A future manager inbox may summarize outstanding readiness cases only after workflow-specific readiness records exist. Do not recreate the removed Overview Manager Readiness block.

## 4. Role Model

### Warehouse User

Allowed in W14D design:

- Review inbound work.
- Open a PO Receiving Review.
- Inspect item lines, ordered quantity, already arrived quantity, still open quantity, target warehouse, and receiving posture.
- Identify likely arrival issues.
- In a later approved non-mutating phase, prepare arrival-readiness evidence.

Not allowed in W14D:

- Create or submit Purchase Receipt.
- Change PO, supplier, price, tax, payment, or commercial terms.
- Post stock.
- Override manager decisions.
- Send supplier messages.

### Warehouse Manager

Allowed in W14D design:

- Review inbound readiness evidence.
- Decide operational readiness state in a later non-mutating phase if approved.
- Route issues to Procurement or internal warehouse follow-up.
- Confirm whether a future Purchase Receipt draft can be prepared after a separate write-governance phase.

Not allowed in W14D:

- Submit Purchase Receipt.
- Post stock ledger.
- Approve commercial supplier changes.
- Send supplier communication from Warehouse.

### Procurement

Owns:

- Supplier communication.
- Purchase Order commercial terms.
- Supplier disputes.
- PO amendment/cancellation.
- Buying price, terms, and supplier policy.

Receives from Warehouse:

- Arrival discrepancy signal.
- Damaged/wrong/short delivery evidence.
- Quality-check-needed signal.
- Supplier paperwork concern.

## 5. Inbound Arrival States

Use clear operational states. These are readiness states, not stock-document states.

- Expected: supplier delivery is due later.
- Due today: delivery should be watched today.
- Overdue: delivery is past expected date.
- Partially arrived: some quantity has already been received in ERPNext evidence.
- Ready to review: arrival evidence is clear enough for manager review.
- Needs warehouse review: missing warehouse, unclear quantity, or line mismatch.
- Needs Procurement follow-up: supplier/PO issue, wrong item, missing supplier paperwork, or PO mismatch.
- Needs quality/damage review: damage, suspected defect, or inspection requirement.
- Restricted detail: the user can see the shell but not all details.

Do not use:

- Receive now.
- Post receipt.
- Create Purchase Receipt.
- Submit.
- Approve stock.
- Supplier send.

## 6. Data Model Strategy

W14D should not create new data yet.

Future non-mutating readiness capture, if approved, should use a separate custom readiness record or controlled server-side event log, not direct mutation of Purchase Order or Purchase Receipt.

Candidate future readiness record fields:

- source_doctype: Purchase Order.
- source_name: Purchase Order name.
- line_keys: selected PO item row names.
- arrival_state: ready, needs_review, needs_procurement_followup, needs_quality_review, restricted.
- evidence_summary: controlled text, length-limited.
- issue_codes: shortage, overage, damage, wrong_item, missing_warehouse, missing_supplier_document, quality_required.
- actor: server-derived session user.
- actor_role_family: Warehouse User or Warehouse Manager.
- created_at and reviewed_at.
- status: draft, submitted_for_manager_review, manager_reviewed, closed.

Rules:

- Never store or accept valuation, rate, amount, tax, supplier pricing, billing, or accounting fields.
- Never trust client-supplied role/user.
- Never write to Purchase Order in W14D.
- Never create Purchase Receipt in W14D.

## 7. Receiving Review UI Design

Use the confirmed premium design direction from Overview, Inbound Receiving, and Receiving Review.

Recommended structure:

- Header: Receiving Review title, PO reference, read-only receiving posture, Back, Refresh.
- Identity strip: supplier, target warehouse, expected date, receiving state.
- Receiving posture panel: line readiness and receipt posture grouped inside one professional card.
- Item Lines tab: default tab showing line-level ordered/arrived/open/warehouse facts.
- Receipt History tab: bounded evidence only, with empty state when there is no receipt history.
- Future Arrival Readiness panel: hidden until a later approved phase; if added, it must be clearly non-mutating.

Do not add action buttons inside W14D.

If future readiness actions are approved, labels should be:

- Prepare readiness note.
- Send for manager review.
- Mark review needed.
- Clear readiness note.

Do not use:

- Receive.
- Create receipt.
- Submit receipt.
- Post.
- Approve receipt.

## 8. Queue UI Design

Inbound Receiving Queue should remain the daily board.

Recommended behavior:

- Keep filters for PO, supplier, warehouse, receiving state.
- Keep summary cards: Due Today, Overdue, Partially Received, Expected Soon.
- Empty states should use the confirmed calm empty-row style.
- Data cards should use the confirmed minimal premium card style.
- Action order on rows should stay detail-first:
  - View lines.
  - Open receiving review.

Reason:

- Viewing lines is a lower-commitment review action.
- Opening receiving review is the deeper object page.

## 9. Backend Readiness Requirements For Future Implementation

If a later phase implements non-mutating readiness capture:

- Add one server method at a time.
- Server validates active session role.
- Server validates user can read the Purchase Order.
- Server recomputes PO open quantity from the database.
- Server rejects hidden or unauthorized lines.
- Server rejects quality/serial/batch flows unless explicitly supported.
- Server writes only the approved custom readiness record or event log.
- Server never creates, updates, or submits Purchase Receipt.
- Server never exposes valuation or commercial fields.

## 10. Smoke And Evidence Requirements

When runtime begins, every phase must include:

- Warehouse Manager and Warehouse User coverage.
- Desktop/laptop/mobile screenshots.
- Empty, restricted, and data-present states where possible.
- No native route escape assertions.
- No write/mutation API assertions.
- No valuation/accounting/commercial assertions.
- No Purchase Receipt creation/submission assertions.
- Back/Refresh/idempotency/stale-response checks if a new async route or panel is introduced.

## 11. Future Phase Split

Recommended sequence after W14D design review:

1. W14D1: Receiving Review UI readiness panel design only, no save.
2. W14D2: Non-mutating arrival readiness capture design, manager/user role gates, no stock document.
3. W14D3: Runtime implementation of non-mutating readiness capture only if owner approves.
4. W14D4: Operation/Security review of readiness capture.
5. W14H: Write governance decision for Purchase Receipt draft creation.
6. W15 or later: Purchase Receipt draft creation pilot, manager-only, no auto-submit, only after separate approval.

## 12. Acceptance Checklist

W14D design is acceptable when:

- It preserves the read-only Warehouse baseline.
- It does not add buttons or code that imply receiving execution.
- It explains how Warehouse, Procurement, and Manager roles interact.
- It chooses Receiving Review as the first workflow page instead of adding a random new page.
- It identifies the future non-mutating readiness record as separate from ERPNext stock documents.
- It keeps Purchase Receipt draft/create/submit out of scope.

## 13. Recommended Next Action

Owner and Operation Reviewer should review this design before any W14D runtime work.

If accepted, the next implementation prompt should be W14D1:

- receiving-review visual readiness panel only;
- no backend write;
- no new top-level page;
- no Purchase Receipt language;
- no Sales or Procurement runtime changes.
