# Procurement Console Phase 5A/5B Managed Buying Baseline

Date: 2026-05-15

Accepted source commit: `af100f9a19e888693ec7c7579503e0699593ba43`

## Purpose And Scope

This document closes Procurement Phase 5A and Phase 5B as the stable protected managed-buying baseline.

Phase 5A delivered the managed Purchase Request form for internal purchase demand capture. Phase 5B delivered the managed RFQ form for direct sourcing-request draft capture. Both flows are productized Procurement Console surfaces and are protected as accepted behavior for future Procurement work.

This baseline does not include Supplier Quotation managed forms, Purchase Order managed forms, PR-to-RFQ conversion, submit/approval workflows, receiving, billing, payment, Item Price mutation, or Default Supplier mutation.

## Accepted Managed Routes

- Purchase Request create route: `/desk/procurement-console-purchase-request-form/new`
- Purchase Request saved/edit route: `/desk/procurement-console-purchase-request-form/<material-request>`
- RFQ create route: `/desk/procurement-console-rfq-form/new`
- RFQ saved/edit route: `/desk/procurement-console-rfq-form/<request-for-quotation>`
- Productized Purchase Request review remains available after save through the accepted review route.
- Productized RFQ review remains available after save through the accepted review route.

Native ERPNext Purchase Request and RFQ create pages are not primary productized create targets after this baseline.

## Accepted User Flows

The following create flows are accepted and protected:

- Procurement Overview `New Purchase Request` opens the managed Purchase Request form.
- Purchase Request Directory `New Purchase Request` opens the same managed Purchase Request form.
- Procurement Overview `New RFQ` opens the managed RFQ form.
- RFQ Directory `New RFQ` opens the same managed RFQ form.
- `Save Request` records a draft/internal Purchase Request using ERPNext document APIs.
- `Save RFQ` records a draft RFQ using ERPNext document APIs.
- After a saved Purchase Request or RFQ, the user may open the productized review route.
- After save only, `Open ERP Form` may appear as a secondary governed native exception if the user has permission.

The accepted flows do not submit, send, approve, reject, convert, receive, bill, pay, update Item Price, or set Default Supplier.

## Accepted UI Contracts

Managed Purchase Request and managed RFQ use the accepted shared managed-form visual language:

- Compact productized header with business-facing kicker, title, subtitle, and status chips.
- Primary save action:
  - Purchase Request: `Save Request`
  - RFQ: `Save RFQ`
- Secondary actions:
  - `Back to Purchase Requests` or `Back to RFQs`
  - `Reset`
  - `Open ERP Form` after save only
  - Productized review action after save only
- No `Submit`, send email, supplier portal, Supplier Quotation creation, Purchase Order creation, receiving, billing, or payment actions.
- No large company field in the single-company UI context.
- No random gradients or decorative backgrounds outside accepted shared-token styling.
- No duplicate Frappe page shell, stale chrome, or stacked managed-form shell.

## Required Date Contract

Both forms use a two-level required-date model:

- Header/detail field: `Default Required By`
- Item-line field: `Line Required By`
- Helper copy: `New item lines use the default date unless changed.`

Line dates follow the accepted inherited/manual rule:

- New item lines inherit the current `Default Required By`.
- Existing item lines that still inherit the header date update immediately when `Default Required By` changes.
- Existing item lines manually changed by the user are not overwritten by later header date changes.
- Adding a new line after a header date change uses the current header date and starts as inherited.

This behavior is accepted for both managed Purchase Request and managed RFQ.

## Item-Line Layout Contract

The managed item-line layout is accepted as follows:

- At 1440px desktop width, item lines use one shared header row: `Item | Qty | Line Required By | Warehouse | UOM | Action`.
- At 1136px laptop width, the responsive two-line row/header treatment is acceptable.
- Repeated per-row labels are not shown on desktop/tablet layouts where the shared header row is active.
- Narrow/mobile layouts may use inline/repeated labels if needed for readability.
- `Add line` remains visually connected to the item section.
- Remove actions remain visible, secondary, and inside the viewport.

## UOM Display Contract

The UOM display is read-only metadata.

- Empty/new line UOM placeholder displays exactly `Derived`.
- `Derived` must not be clipped, split, wrapped, or awkwardly letter-spaced.
- Selected or saved item UOM values such as `Nos` must display cleanly.
- UOM is not an editable user input in the productized managed form.

## Autocomplete Overlay Contract

Accepted autocomplete behavior:

- Purchase Request item autocomplete opens as a floating overlay attached to the active item input.
- RFQ supplier, item, and warehouse autocompletes open as floating overlays attached to their active inputs.
- Overlays are not clipped by form cards or table containers.
- Overlays do not cause layout shift.
- Overlays remain above the form/table layer with the accepted z-index, surface, border, and shadow treatment.

## Permission Expectations

- Purchase Manager and Purchase User may use the managed forms only when ERPNext DocType permissions allow the corresponding create/read/write behavior.
- Procurement role family alone is not sufficient if ERPNext DocType permission denies access.
- Sales-only roles must not receive Procurement managed-buying access unless they also hold the required Procurement and ERPNext permissions.
- Guest or unauthenticated users remain restricted.

## Native Exception Boundary

`Open ERP Form` is a governed native exception after a draft Purchase Request or RFQ has been saved. It is not the primary create route.

The productized create actions from Overview and the relevant directory pages must not route to raw ERPNext native create pages for Purchase Request or RFQ after this baseline.

Existing governed native exceptions for future document types remain outside this baseline until their managed replacements are explicitly implemented and accepted.

## Deferred Scope

The following work remains explicitly deferred:

- Phase 5C
- Managed Supplier Quotation form
- Managed Purchase Order form
- PR-to-RFQ conversion
- RFQ submit/send email/supplier portal
- Supplier Quotation creation from RFQ
- Purchase Order creation from RFQ, Supplier Quotation, or Purchase Request
- Submit, approve, reject, cancel, amend, stop, or close workflows
- Warehouse receiving
- Purchase Invoice, billing, payment, or accounting execution
- Item Price mutation
- Default Supplier mutation
- Supplier or Item master create/edit

## Validation Evidence

Accepted final commit:

- `af100f9a19e888693ec7c7579503e0699593ba43`

Accepted focused live smoke artifacts:

- `/tmp/managed-buying-line-repair-live-final-20260514T175427Z`

Accepted Sales freeze artifact:

- `/tmp/sales-freeze-protection-20260514T175557Z`

Accepted protected workspace gate artifact:

- `/tmp/protected-workspaces-20260514T175940Z`

Accepted source/live hashes:

- Managed Purchase Request form: `72e4eca0e9a9c8850579eea9f695f7bf77534634d96ec6f1ddeaffcfbc5f59a0`
- Managed RFQ form: `f9288f8df2438db20f91c33214f8f7ec02bad3394475c34fbbfa9c635c51aa54`

## Future Phase 5C Warning

Future managed Supplier Quotation, managed Purchase Order, or conversion work must treat this Phase 5A/5B behavior as protected baseline behavior.

Any future shared runtime, shared CSS, managed-form shell, navigation, action registry, or smoke-contract change that can affect this baseline must update protection tests where appropriate and pass the protected workspace gate before acceptance.

