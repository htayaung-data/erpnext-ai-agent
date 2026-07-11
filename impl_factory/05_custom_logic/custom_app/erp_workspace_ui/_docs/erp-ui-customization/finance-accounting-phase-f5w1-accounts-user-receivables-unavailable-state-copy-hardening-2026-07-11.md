# Finance & Accounting F5W1: Accounts User Receivables Unavailable-State Copy Hardening

Date: 2026-07-11
Status: Source-only manual-review remediation

## Decision

Finance role, company, query, and accounting behavior remain unchanged. Internal Receivables policy reasons remain available in backend policy metadata but are not assembled into user-facing cards.

## Visible Copy Contract

- Accounts User sees a manager-only Receivables explanation without `low_count_policy_not_ready` or another internal reason code.
- Manager source failures use generic unavailable business copy.
- No customer, invoice, voucher, account, report, export, or action data is shown from an unavailable response.
- The frontend replaces snake-case policy codes in an unavailable Receivables card before rendering.
- Existing Accounts Manager aggregate Receivables posture and Payables unavailable copy remain unchanged.

## Boundaries

F5W1 adds no AR or AP query, amount, row, identity, native report, route, export, or execution behavior. It does not change roles, company scope, permissions, posting, payment, reconciliation, write-off, tax, close, notification, email, portal, or external action behavior.

## Review Status

F5W final manual acceptance remains separate. This source patch does not approve live alignment, restart, cache clear, metadata reload, migration, staging, commit, push, or protected gates.

## Validation Contract
