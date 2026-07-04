# Warehouse Console Phase W16G5J - Shared Workflow Page System

Date: 2026-07-03

## Scope

W16G5J standardizes the active custom workflow page grammar for:

- Returns Work Hub
- Internal Transfer workflow
- Cycle Count workflow

This phase is source/UI/smoke/documentation only. It does not add backend methods, DocType metadata, ERP document runtime, stock/accounting mutation, notification behavior, or native ERP route exposure.

## Changes

- Added shared workflow page shell, page header, workflow card, mode badge, guardrail, body, and panel data attributes.
- Kept Returns-specific selectors for the Returns Work Hub where they are still compatibility anchors.
- Moved Internal Transfer and Cycle Count high-level page structure onto shared `warehouse-workflow-*` classes instead of depending on Returns hub layout grammar.
- Shortened workflow header copy so pages read as operational custom workflows, not design placeholders.
- Compact guardrail copy remains explicit, but less repetitive.
- Extended W9A smoke assertions to require the shared workflow page system on all three active custom workflow pages.

## Boundaries

W16G5J does not approve or introduce:

- Stock Entry, Purchase Receipt, Delivery Note, Stock Reconciliation, Pick List, or Stock Reservation lifecycle behavior
- stock movement, stock posting, reserve, unreserve, ledger, balance, or valuation updates
- native ERPNext route exposure
- Sales, Procurement, Finance, Inventory/Admin runtime mutation
- notification, email, portal, or external action behavior
- live alignment, restart, commit, push, or Warehouse Custom Workflow Closure

## Manual Review

Owner manual review is still required after live alignment because this is a visible UI consistency phase.

Review the following pages:

- Returns
- Internal Transfer
- Cycle Count

Expected result:

- Each page uses the same premium workflow page framing.
- Guardrails are visible but compact.
- Workflow controls still save or mark custom Warehouse records only.
- No ERP document action is visually implied.
