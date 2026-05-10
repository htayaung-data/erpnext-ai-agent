# Shared Reports Index Navigation Standard v1

Date: 2026-05-10
Status: Mandatory shared navigation standard
Applies to: Procurement Console Phase 4A and future ERP Workspace UI workspaces

## Purpose

ERP Workspace UI report navigation must scale without turning the sidebar into a report catalog. The sidebar is for stable workspace destinations. Individual reports belong inside a productized Reports Index unless a documented operational exception is approved.

## Core Rule

Workspaces with three or more meaningful reports must expose one `Reports` sidebar destination.

Individual reports must live inside the Reports Index. The sidebar must not list every report individually.

Allowed sidebar report exceptions:

- A daily operational command-center report may be promoted to the sidebar only when it is documented as an exception.
- The exception must explain why the report is used as a primary operating surface, not just a catalog item.
- The report must still route to a productized report page, not a raw ERPNext report URL.

Overview pages may show one to three priority report shortcuts. Overview must not become the full report catalog.

## Reports Index Requirements

Report cards must support these states:

- `ready`: opens an approved productized report route.
- `planned`: visible as roadmap context but disabled; it must not navigate.
- `restricted`: visible or hidden according to role/scope policy and must not leak inaccessible data.
- `unavailable`: visible only when useful and must show controlled unavailable state.

Report cards must route only to productized report pages such as:

```text
/desk/<workspace-report-route>/<report-key>
```

Planned, restricted, and unavailable cards must not leak to raw native report pages or broken routes.

Native ERPNext reports may be used only through governed wrappers that preserve productized workspace chrome, role checks, state kinds, and mutation boundaries.

Raw ERPNext report URLs are forbidden as primary navigation.

## Procurement Phase 4A Application

Procurement now has one sidebar report destination:

- `Reports` -> `/desk/procurement-console-report`

`Quote Comparison` remains the first ready card inside Procurement Reports Index and keeps its stable direct route:

```text
/desk/procurement-console-report/supplier-quotation-comparison
```

The standalone `Quote Comparison` sidebar item is not part of the enterprise pattern and must not be restored unless approved as a documented command-center exception.

Phase 4A must not implement Purchase Order Analysis or any other planned report as part of this navigation cleanup.

## Sales Legacy Exception

Sales Console is frozen as `sales-console-freeze-v2`. Sales still has frozen legacy report shortcuts and must not be migrated under this Procurement navigation task.

Sales report navigation should be aligned to this standard only in a future protected Sales alignment task that runs the Sales freeze protection gate and receives owner approval.

## Future Workspace Rule

Future workspaces must start with this pattern:

1. One `Reports` sidebar destination when the workspace has three or more meaningful reports.
2. Individual report cards inside Reports Index.
3. Stable direct productized report URLs.
4. No raw ERPNext report URLs as primary navigation.
5. Planned cards disabled until their productized report is implemented.
