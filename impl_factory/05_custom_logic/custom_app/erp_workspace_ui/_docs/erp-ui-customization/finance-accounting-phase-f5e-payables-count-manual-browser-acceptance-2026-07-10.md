# Finance & Accounting Phase F5E - Payables Count Manual Browser Acceptance

Date: 2026-07-10
Status: accepted manual browser outcome; count-only and fail-closed
Workspace family: Finance & Accounting
Page label: Finance Control Desk
Live route reviewed: `/desk/finance-control-desk`

## Decision

Owner/Main Control accepts the current live Payables posture as controlled unavailable when the backend returns `payment_terms_not_supported`.

This is the safe result for the approved first count model. At least one open Purchase Invoice uses a payment terms template, and F5C deliberately does not interpret payment schedules. Returning no AP counts is safer than presenting due-date buckets that could omit or mis-age scheduled supplier liabilities.

The manual result accepts the count-only boundary and its fail-closed behavior. It does not accept payment-schedule support, AP amount exposure, row-level Payables data, native ERP surfaces, or payment/accounting execution.

## Naming Traceability

The original F5 design reserved `F5D` for manager-only AP amount source proof and `F5E` for manager-only AP amount runtime. Neither amount phase occurred.

Later operational work used `F5D` for count-only live alignment, `F5D1` for the live gate diagnostic, and this `F5E` artifact for manual acceptance. This operational naming does not relabel history and does not imply that the original AP amount proof or amount runtime was completed. Any future AP amount work requires a separately named source-policy/proof phase, explicit Owner/Main Control approval, and a new runtime approval.

## Accepted Live Evidence

For `finance.lead@meet.com`:

- the Finance Control Desk route loaded without a Page, Company field, User Permission, or aggregate-query modal;
- the user passed the `Accounts Manager` gate;
- the Finance resolver selected `Mingalar Mobile Distribution Co., Ltd.` through `single_company_site_fallback`; Owner acceptance of this fallback is limited to the current single-company F5 count-only scope;
- Purchase Invoice read permission was verified;
- the Payables source returned controlled unavailable with `payment_terms_not_supported`;
- no bucket counts or partial posture were returned after that gate.

For `accounts.ygn.01@meet.com`:

- the Finance Control Desk remains available as the approved Finance landing;
- `Accounts User` does not receive Accounts Manager-only AP bucket counts;
- no AP amount or row-level Payables data is enabled.

## What This Posture Is Not

The accepted live state is not:

- an Accounts Payable aging total;
- an AP balance or supplier liability balance;
- a cash requirement or cash forecast;
- payment approval or payment authority;
- a supplier worklist or invoice worklist;
- a native ERPNext Accounts Payable report;
- evidence that payment schedules are supported;
- evidence that AP amount source semantics have been proven.

## Data And Action Boundary

The live page displays none of the following Payables data:

- AP amount values or currency totals;
- supplier names, IDs, balances, contacts, bank details, or tax details;
- Purchase Invoice names, bill references, dates, line items, or statuses;
- Payment Entry, Payment Request, or Payment Order rows or identifiers;
- account, voucher, Payment Ledger Entry, or GL Entry rows or identifiers.

The page also exposes no native report, route, export, download, print, payment action, Purchase Invoice lifecycle action, Payment Entry lifecycle action, Journal Entry, GL mutation, reconciliation, write-off, tax, close, email, notification, portal, supplier communication, or external action.

## Residual Caveat

F5C checks `payment_terms_template` and fails closed when it is present. It does not read Payment Schedule child rows. A schedule without a template remains an unresolved semantic case and must stay outside the approved count model until a separate source-policy/proof phase is accepted.

## Acceptance Boundary

This document records manual acceptance of the controlled-unavailable live result only. It does not approve staging, commit, push, protected gates, live realignment, restart, cache clear, metadata reload, migration, payment-schedule implementation, AP amount proof/runtime, rows, native ERP surfaces, or accounting execution.
