# Finance & Accounting Phase F4K1 - AR Copy And Traceability Remediation

Date: 2026-07-07
Status: source-only copy and documentation remediation
Depends on: F4K stopped gap report
Workspace family: Finance & Accounting
Visible page label: Finance Control Desk

## Decision

F4K1 remediates the High gaps identified in F4K before any live-alignment prep can be reconsidered.

F4K1 changes copy and documentation only. It does not add data sources, rows, customer lists, invoice lists, voucher detail, account detail, Payment Ledger row detail, GL detail, native reports, routes, exports, downloads, print, posting, payment, reconciliation, write-off, tax, close, email, notification, portal behavior, live alignment, restart, metadata reload, protected gates, commit, or push.

## Remediated Gaps

### Bounded Aggregate Source Reads vs Row-Level Exposure

The Finance page and backend posture copy now distinguish:

- allowed server-side bounded aggregate source reads used to build approved posture;
- forbidden row-level financial data returned to the browser;
- forbidden row-level data shown, linked, exported, or made actionable.

Required wording contract:

- use `row-level data is not returned, shown, linked, exported, or actionable`;
- use `bounded aggregate source reads` only to explain backend aggregation;
- avoid `no financial rows loaded` because it can imply the backend performs no aggregate source reads;
- keep no-effect and no-execution copy visible but compact.

### Count-vs-Amount Source Wording

The Finance receivables posture must describe counts and amounts as separate aggregate signals:

- receivables count posture: `Sales Invoice aggregate count buckets`;
- manager-only amount posture: `Payment Ledger MMK amount buckets`;
- combined posture: related aggregate posture, not a reconciled accounting report;
- amount-only posture: Sales Invoice count buckets may be unavailable while manager-only Payment Ledger MMK amount buckets are ready.

This wording is intentionally source-explicit for Owner/manual review. It does not expose document names, customer names, voucher names, account names, Payment Ledger row identifiers, native routes, reports, exports, or execution controls.

### F4G-To-F4J Provenance

F4G remains the design-only Payment Ledger aggregate contract. It did not itself approve runtime amount exposure.

The later source progression is:

- F4H: implemented manager-only aggregate MMK Payment Ledger amount posture from the F4G contract.
- F4H1: added bounded pagination and source-size fail-closed protection.
- F4I1: remediated due-date semantics, payment-term unsupported policy, public payload context exposure, copy mismatch, stale shell/sidebar copy, and split receivable account fixture coverage.
- F4J: performed final source review and remediated allocation-side split receivable account fail-closed behavior plus amount-ready/count-unavailable card copy.
- F4K: stopped live-alignment-prep readiness because copy and provenance were not clear enough.
- F4K1: remediates those copy and provenance gaps while keeping live alignment blocked.

## Current Source Contract After F4K1

Accounts Manager may see, when all gates pass:

- aggregate receivables count buckets from Sales Invoice count reads;
- manager-only aggregate MMK amount buckets from Payment Ledger voucher-outstanding semantics;
- suppressed amount buckets where low-population rules apply.

Accounts Manager must not see:

- customer rows or customer identifiers;
- invoice rows or invoice identifiers;
- voucher, account, Payment Ledger, or GL row detail;
- native report, Form, List, or query-report routes;
- export, download, or print controls;
- posting, payment, reconciliation, write-off, tax, close, email, notification, portal, or execution controls.

Accounts User and non-finance users remain blocked from amount posture. Accounts User raw count visibility remains blocked until a later low-count/coarsening policy is approved.

## Manual Review Checklist

Owner/Main Control should verify:

- the page says aggregate posture, not execution;
- the page does not say `No financial rows loaded`;
- visible copy states row-level data is not returned, shown, linked, exported, or actionable;
- receivables counts are described as Sales Invoice aggregate count buckets;
- manager amounts are described as Payment Ledger MMK amount buckets;
- combined count/amount posture is not presented as a reconciled report;
- restricted users do not see the full Finance posture;
- no native routes, reports, exports, print/download, customer/invoice/voucher/account/PLE/GL identities, or action controls appear.

## Remaining Caveats

- Payment Ledger semantic drift still requires manual verification before live alignment.
- Payment terms remain unsupported and fail closed only when detected through the current policy path.
- Missing due-date Sales Invoice count behavior remains an Owner review item.
- Split receivable accounts fail closed and require a later policy if the business needs support.
- Low-population suppression thresholds remain Owner-reviewable.
- F4K1 does not approve live alignment.

## Recommended Next Step

If validation passes and Owner accepts F4K1, the next step may be `F4L Finance AR Source Package Manual/Live-Alignment Prep Recheck`.

Do not proceed to live alignment, restart, metadata reload, protected gates, commit, push, Payables implementation, GL/Cash/Tax/Close work, row drilldown, native reports/routes, exports, or accounting execution without explicit Owner/Main Control approval.
