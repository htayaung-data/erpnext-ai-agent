# Freeze Note: Sales Invoice

Date: 2026-04-16

Status:

- Frozen for current phase

Scope:

- submitted Sales Invoice child page
- invoice snapshot, invoice lines, settlement focus, payments, terms, more info, and connections

## Freeze decision

Sales Invoice is accepted as the billing and settlement page.

It is approved because the page now separates commercial commitment from financial execution in a usable way.

## What is accepted

### 1. Details tab is correctly focused

- invoice snapshot frames customer, posting, due date, and settlement state
- invoice lines stay close to ERP authority while still receiving productized reading support
- settlement focus helps the user understand outstanding, settled, payment-entry count, and due-date posture

### 2. Payment boundary is acceptable

- `Payments` is the right place for settlement execution
- payment structure remaining under `Terms` is accepted because it describes commitment structure, not live collection activity

### 3. More Info and connections are good enough

- `More Info` was simplified so it does not pretend to be more valuable than it is
- `Connections` supports upstream and downstream movement without turning into another dashboard

### 4. Permission-aware behavior is accepted

- when payment-entry visibility is restricted, the page should degrade safely instead of breaking the overall invoice workspace

## Accepted deferred items

- later refinement of permission-aware fallback copy if real user roles require it
- one final consistency pass with the other child pages

## Reopen conditions

Reopen only if:

- settlement signals stop matching actual invoice state
- permissions cause the page shell to fail instead of degrading safely
- payments, terms, and more-info boundaries become mixed again
- action priority stops reflecting real billing workflow
