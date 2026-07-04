# Warehouse Console Phase W16G5C - Custom Workflow Record Recall and Manager Review Rehydration

Date: 2026-07-03

## Phase Purpose

W16G5B identified that Returns, Internal Transfer, and Cycle Count custom workflows could save records correctly but lost the saved-record identity after page refresh, route reload, or a new sign-in. That meant manager posture controls depended on page-local JavaScript state instead of persisted custom Warehouse records.

W16G5C fixes that persistence gap without activating ERPNext stock/accounting document workflows.

## Implementation Summary

W16G5C adds read-only workflow state endpoints for the dedicated custom workflow pages:

- `get_warehouse_returns_work_hub`
- `get_warehouse_internal_transfer_workflow`
- `get_warehouse_cycle_count_workflow`

Each endpoint returns bounded recent summaries from app-owned custom Warehouse records only. The frontend page loaders now call these page-specific state endpoints instead of reusing the generic Overview payload. When a saved custom record exists, the page hydrates the relevant record id into the existing manager-control gating so manager review can continue after refresh or a new sign-in.

## Business Behavior

- Returns Work Hub recalls the latest accessible custom customer intake and supplier candidate records.
- Internal Transfer recalls the latest accessible custom internal transfer candidate.
- Cycle Count recalls the latest accessible custom cycle count task.
- Manager controls remain role-gated and record-gated.
- If no custom record exists, manager controls stay disabled and the page continues to ask for a custom record first.

This phase intentionally uses latest-record auto-recall only. A multi-record selector/search queue remains a possible future UX enhancement if owners need to review multiple open custom records from one page.

## Security and Stability Boundaries

W16G5C remains custom-record-only and read-mostly except for existing already-approved save/manager methods. The new state endpoints:

- require authenticated Warehouse access;
- filter recalled records through visible warehouse checks;
- return bounded summaries only;
- expose no native ERP routes;
- return safe false no-effect flags for stock, ledger, balance, reservation, reconciliation, and valuation;
- do not create, save, submit, cancel, amend, or delete ERPNext stock/accounting documents;
- do not notify customers or suppliers;
- do not change Sales, Procurement, Finance, Inventory, or Admin runtime behavior.

## Tests Added

- Contract tests verify saved custom records are recalled by the new endpoints.
- Restricted non-Warehouse roles receive restricted payloads and no custom record queries.
- Registry tests lock the new read-only endpoint names.
- W9A smoke now models persisted custom records and refreshes pages before exercising manager posture paths.

## Remaining Scope Before Warehouse Custom Workflow Closure

W16G5C is not Warehouse Custom Workflow Closure. It resolves the saved-record recall blocker that prevented honest closure readiness. W16G5D/W16H still need final quality gate review, owner manual acceptance, and explicit closure documentation before W16H can close the custom workflow foundation. Whole Warehouse production execution remains deferred to W17+.

## Explicitly Not Approved

- Stock Reconciliation runtime or draft creation.
- Stock Entry runtime or draft creation.
- Purchase Receipt, Delivery Note, Sales Return, Credit Note, Purchase Invoice return, debit note, or other ERPNext document lifecycle action.
- Stock Ledger, Stock Balance, Stock Reservation, reserve/unreserve, stock posting, or stock movement mutation.
- Native ERP route exposure.
- Valuation, accounting, commercial, pricing, margin, payment, tax, or GL exposure.
- Customer/supplier notification, email, portal, or external action.
- Sales or Procurement runtime mutation.
- Live alignment, restart, protected gate, commit, push, or release closure.
