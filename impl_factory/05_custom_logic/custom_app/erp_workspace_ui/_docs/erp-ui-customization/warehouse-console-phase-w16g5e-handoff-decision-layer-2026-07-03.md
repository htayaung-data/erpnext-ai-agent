# Warehouse Console Phase W16G5E - Handoff Decision Layer

Date: 2026-07-03

## Purpose

W16G5E closes the owner-facing handoff wording gap found during W16G5 review. The Warehouse Console already has custom evidence, manager posture, and request-only backend foundations, but the dedicated workflow pages must not look like they start Sales, Procurement, Inventory/Admin, dispatch, or ERP document actions when they only save custom Warehouse posture.

## Decision

Keep W16G5E as a handoff honesty and posture-label phase. Do not activate any new `request_warehouse_*_handoff` UI action in this phase.

Reasons:

- Handoff request methods exist in backend foundations, but the current workflow pages do not call them.
- Activating request-handoff UI is a larger business process decision and needs separate owner/security acceptance.
- The safer W16G5E fix is to make visible controls say what they actually do: mark custom posture or review-needed state only.

## Scope Implemented

- Receiving manager control wording now says `Mark Procurement review needed`, not `Escalate to Procurement`.
- Picking manager control wording now says `Mark Sales review needed` and `Mark outbound readiness`, not `Escalate to Sales` or `Record handoff review`.
- Returns manager controls now say `Mark Sales review needed` and `Mark Procurement review needed`.
- Internal Transfer and Cycle Count manager controls now say `Mark Inventory/Admin review needed`.
- Backend custom status labels now use review/posture wording:
  - `Procurement Review Needed`
  - `Sales Review Needed`
  - `Finance/Admin Review Needed`
  - `Inventory/Admin Review Needed`
  - `Outbound Review Ready`
- Smoke source guard rejects stale owner-facing labels such as `Escalate to Sales`, `Escalate to Procurement`, `Request Inventory/Admin review`, `Record handoff review`, `Document owner review`, and `outbound handoff readiness`.

## Explicitly Not Implemented

- No new request-handoff UI button was activated.
- No `request_warehouse_*_handoff` frontend call was added.
- No ERPNext document creation, save, submit, cancel, amend, or delete was added.
- No Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, return Purchase Receipt, debit note, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, or Stock Reservation action was added.
- No stock movement, stock posting, reserve/unreserve, valuation/accounting/commercial exposure, native ERP route, notification, email, portal, or external action was added.

## Owner Manual Check

Manual check is useful after live alignment because owner-facing workflow labels changed. Confirm each page reads as custom posture only:

- Receiving Review: Procurement wording should read as review-needed posture only.
- Picking Review: Sales and outbound wording should not imply dispatch, handoff execution, Delivery Note, Pick List, or Stock Reservation.
- Returns Work Hub: Sales and Procurement manager controls should not imply customer/supplier notification or ERP return document creation.
- Internal Transfer: Inventory/Admin manager control should not imply Stock Entry or transfer execution.
- Cycle Count: Inventory/Admin manager control should not imply Stock Reconciliation or stock adjustment.

## Next Step

After source validation and review, W16G5F should perform the final quality gate and owner page-by-page manual review before W16H Warehouse Custom Workflow Closure.
