# Freeze Note: Sales Order

Date: 2026-04-16

Status:

- Frozen for current phase

Scope:

- submitted Sales Order child page
- details, address and contact, terms, more info, and connections
- action band, guidance band, and related-document movement

## Freeze decision

Sales Order is accepted as a premium execution page.

It is approved because the page now balances three things correctly:

- commercial overview
- operational follow-through
- related-document navigation

## What is accepted

### 1. Header and action architecture

- top summary, action band, and guidance are strong enough to anchor the page
- the page lands in the correct productized context instead of dropping the user into native noise

### 2. Tab structure is enterprise-usable

- `Details` gives execution context, commercial summary, and readable line focus
- `Address & Contact` is standardized and no longer feels improvised
- `Terms` keeps payment structure and customer-facing conditions in the correct place
- `More Info` is reduced to useful secondary information, not decoration
- `Connections` is treated as the system-of-record view for linked document movement

### 3. Connections design is approved

- the Sales Order connections workspace became the source pattern for later pages
- it is accepted as the reference model for fulfillment and available-path presentation

### 4. Data duplication was reduced

- duplicate or low-value fields were intentionally demoted or removed where they created noise
- line-level delivery date is suppressed in draft mode when it only repeats the header date

## Accepted deferred items

- one later spacing-rhythm pass across all finalized child pages
- non-blocking performance polish if shared runtime improvements become available

## Reopen conditions

Reopen only if:

- connections stop reflecting actual downstream movement
- related-document navigation becomes unreliable
- address/contact or terms regress back into inconsistent layout
- duplicate/noisy detail fields reappear and reduce usability
