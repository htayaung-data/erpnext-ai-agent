# Sales Console Business Copy Contract v1

Date: 2026-04-26

## Purpose

Sales Console pages should feel like an operating console, not a training manual. Section titles, chips, metrics, and field labels should carry the normal reading load. Helper text is allowed only when it changes the user's business decision or reduces operational risk.

## Rendering Rule

Neutral section descriptions are quiet by default in shared child-page renderers.

A note must opt into one of these business intents before it renders:

- `action`: tells the user the next useful action.
- `blocked`: explains why progress is blocked.
- `decision`: helps choose between business paths.
- `empty`: explains why a meaningful area has no records yet.
- `exception`: highlights an unusual state.
- `missing`: identifies required missing setup.
- `readonly`: explains why a user cannot edit.
- `risk`: warns about business or operational risk.
- `warning`: calls attention to a non-blocking issue.

## What To Avoid

- Do not write notes that simply restate the heading.
- Do not mention implementation details such as "native ERP", "authoritative totals", or "workspace renderer".
- Do not add static prose under every card or section for visual symmetry.
- Do not use color-only signals without a text label or status chip.

## Preferred Pattern

- Use a clear title first.
- Use status chips and metrics for normal business state.
- Use short notes only for missing, exception, blocked, empty, or readonly states.
- Keep document relationship guidance inside Connections only when it helps distinguish linked document types or empty states.

## Current Implementation

The shared policy lives in:

- `erp_workspace_ui/public/js/runtime/child_page/child_page_helpers.js`
- `erp_workspace_ui/public/js/runtime/child_page/child_page_sections.js`
- `erp_workspace_ui/public/js/runtime/child_page/child_page_terms.js`
- `erp_workspace_ui/public/js/runtime/child_page/child_page_details.js`
- `erp_workspace_ui/public/js/runtime/child_page/child_page_summaries.js`
- `erp_workspace_ui/public/js/runtime/child_page/child_page_connections.js`

Sales Order is the first full application. Quotation, Sales Invoice, and Delivery Note inherit the same shared renderer behavior where they use these child-page components.
