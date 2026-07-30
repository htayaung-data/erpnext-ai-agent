# Finance Cycle 2 GL/TB Blank Default Finance Book Contract Amendment

Date: 2026-07-30
Status: Owner-approved source contract
Decision: A Company with no named Default Finance Book uses an explicit `unbooked_only` GL/TB mode. The Company record is not changed.

## Closed two-mode contract

| Mode | Company Default Finance Book | Eligible GL Entry cohort | Finance Book record lookup | Canonical v2 response |
| --- | --- | --- | --- | --- |
| Named default | One non-empty, trimmed name | The named default, blank, and `NULL` | Required for the named default | `default_finance_book` is the name; `finance_book_scope` is `company_default`, `blank_unbooked`, `null_unbooked` |
| `unbooked_only` | Exact blank or `NULL`, normalized to `null` | Blank and `NULL` only | Skipped because no named default exists | `default_finance_book: null`; `finance_book_scope: ["blank_unbooked", "null_unbooked"]` |

Every other named Finance Book is excluded from `unbooked_only`. There is no selector, implicit all-books behavior, non-default-book expansion, or Accounting Dimension support. Whitespace-only, malformed, cross-mode, reordered, extra, incomplete, or permission-ambiguous values fail closed as `finance_read_unavailable`.

## Preserved invariants

- The internal product schema is `finance-gl-trial-balance.internal.v2`; named-mode output is unchanged except for that schema version.
- Finance Book read authority remains in both permission passes. Only the named record lookup is conditional.
- Opening and movement reads use the same mode-specific cohort and exact completeness predicate.
- Company isolation, cancellation filtering, complete Account hierarchy, GL-account membership, exact debit/credit equations, currency and fiscal boundaries, permission revalidation, primary-connection snapshot continuity, rollback, no-execution posture, and zero active dimensions remain mandatory.
- Policy evidence records named-default presence truthfully and returns only the existing closed aggregate evidence; no names, SQL, exceptions, identities, or dynamic diagnostic content are added.
- The Finance page accepts only the two closed v2 variants and renders a fixed unbooked-only label without displaying `company_default` when no named default exists.

## Delivery boundary

This amendment authorizes source and focused-test publication only. It does not authorize live alignment, configuration or permission changes, endpoint invocation, accounting-data access, policy injection, activation, migration, restart, or authenticated product acceptance.
