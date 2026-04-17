# Freeze Note: Quotation

Date: 2026-04-16

Status:

- Frozen for current phase

Scope:

- submitted Quotation child page
- review posture, commercial posture, customer context, terms, more info, and connections

## Freeze decision

Quotation is accepted as the commercial review page for the sales flow.

It is approved because it now supports the actual business question the user needs to answer:

- is this quote commercially ready
- what does the customer context look like
- what is the downstream conversion state

## What is accepted

### 1. Details tab is now purposeful

- quote snapshot and quoted lines are the center of gravity
- commercial posture presents quantity, amount, tax, and total in a useful way
- pricing diagnostics and missing-price visibility support real sales work instead of hiding issues

### 2. Address and contact structure is standardized

- the page no longer depends on dynamic hide/show layout in a way that breaks structure
- important customer-facing fields are presented in a stable and readable format

### 3. Terms and more-info boundaries are correct

- `Terms` focuses on payment structure and quotation conditions
- `More Info` is kept for secondary context, not to duplicate navigation

### 4. Connections reflect conversion logic

- quotation-to-order-to-fulfillment visibility is clear enough
- relationship context and downstream chain are useful without being overloaded

## Accepted deferred items

- further data-quality improvements for item pricing belong to ERP master data, not this UI layer
- one later consistency pass can still tighten spacing and micro-rhythm

## Reopen conditions

Reopen only if:

- pricing diagnostics stop reflecting actual price availability
- submitted quotation tabs lose the standardized structure
- connection chain stops matching real conversion behavior
- the page falls back into decorative secondary information instead of commercial clarity
