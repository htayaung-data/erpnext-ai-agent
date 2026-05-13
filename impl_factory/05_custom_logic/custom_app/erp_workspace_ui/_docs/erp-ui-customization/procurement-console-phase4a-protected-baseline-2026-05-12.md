# Procurement Console Phase 4A Protected Baseline

Date: 2026-05-12
Status: Protected baseline, not final freeze
Workspace: Procurement Console

## Purpose

Procurement Console remains under active development. This document protects the owner-accepted Phase 4A scope from accidental regression while allowing future Procurement phases to continue under controlled gates.

This is not a final Procurement freeze. Do not describe Procurement Console as complete or frozen. The correct status is Procurement Console Phase 4A Protected Baseline.

## Owner Acceptance

The owner has manually accepted the implemented Procurement Console scope through Phase 4A as premium UI/UX. Future work may extend Procurement, but must not regress the protected surfaces listed below.

## Protected Surfaces

The following surfaces are part of the Phase 4A protected baseline:

- Procurement Overview
- Supplier Directory
- Supplier Detail
- Buying Item Directory
- Buying Item Detail
- Purchase Request Directory
- Purchase Request Review
- RFQ Directory
- RFQ Review
- Supplier Quotation Directory
- Supplier Quotation Review
- Purchase Order Directory
- PO follow-up queues
- Purchase Order Follow-up Detail
- Reports Index
- Quote Comparison
- Purchase Order Analysis
- Demand-to-Order Coverage
- Item Purchase History / Price Review

Protected behavior includes route lifecycle, no page stacking, sidebar selection, shell/header composition, filter behavior, responsive filter layout, report shell behavior, detail/review boundary behavior, governed native exception boundaries, and absence of forbidden mutation leakage on productized pages.

## Accepted Native Exceptions

Existing governed native exceptions remain accepted only where already implemented and classified. These include create/open ERP form paths needed for ERPNext workflow truth and role permissions.

Accepted native exceptions must remain governed by workspace chrome and policy. They must not expand to new native routes or mutation actions without owner approval.

Allowed native workflow controls inside governed exceptions continue to include standard ERPNext document tools such as Save, Cancel where permission allows, Get Items From, child table/grid controls, and document helper controls required by ERPNext workflows.

## Deferred Scope

The following are explicitly deferred and must not be implemented or implied by this protection package:

- Phase 5 managed Procurement forms
- Supplier create/edit management
- Buying item create/edit management
- Supplier scorecard
- Supplier portal
- Warehouse receiving
- Finance billing/payment
- Purchase Order approval/rejection workflow mutation pages
- Item price mutation
- Default supplier mutation

## Baseline Evidence Requirements

A future change that could affect Procurement Phase 4A must preserve evidence for the accepted surfaces. Evidence may include Docker Playwright reports, screenshots, and JSON summaries from the protected workspace gate.

Minimum evidence for protected Procurement changes:

- Procurement smoke for Purchase Manager
- Procurement smoke for Purchase User
- Procurement responsive filter regression for Purchase Manager
- Procurement responsive filter regression for Purchase User
- No duplicate headers or shell stacking
- No page JavaScript errors
- No raw ERPNext report URLs as primary navigation
- No forbidden mutation labels on productized pages

If shared runtime, CSS, boot, registry, list shell, report shell, or child-page shell files are touched, the combined protected workspace gate is mandatory.

## Future Change Rules

Future agents may:

- Add new Procurement phases after owner instruction.
- Extend Procurement reports or managed forms only within the approved phase scope.
- Refactor shared components only if the combined protected workspace gate passes.
- Update documentation when implementation and evidence change.

Future agents must not:

- Regress any protected Phase 4A surface.
- Rename protected routes without owner approval and migration evidence.
- Expand native exceptions without owner approval.
- Add forbidden mutations to productized review/detail/report/worklist pages.
- Treat Procurement as final-frozen or complete.
- Change Sales runtime behavior while working on Procurement.

## Owner Approval Required

Owner approval is required before:

- Expanding native exception scope.
- Adding managed mutation pages.
- Changing protected route keys or sidebar destinations.
- Removing protected report cards or protected direct report URLs.
- Weakening the protected workspace gate.
- Waiving a Procurement protected-baseline failure.

## Required Gates

For Procurement-only protected files:

- Python compile and unit discovery
- Procurement protected baseline smoke for both Purchase Manager and Purchase User
- Procurement responsive filter regression for both Purchase Manager and Purchase User
- `git diff --check HEAD`

For shared files:

- Full protected workspace gate
- Sales freeze protection gate
- Procurement protected baseline smoke
- Procurement responsive filter regression
- Sales directory performance smoke when Sales directory behavior could be affected

For docs-only changes:

- Source validation and doc consistency review are sufficient unless the docs alter contracts, manifests, gates, watchlists, or protected status. Contract or gate docs require the relevant protection gate.

## Current Protection Status

Sales Console remains frozen and protected under Sales Freeze v2/v2.1.

Procurement Console is protected only through Phase 4A accepted baseline. Procurement development may continue, but accepted Phase 4A surfaces are protected against regression.
