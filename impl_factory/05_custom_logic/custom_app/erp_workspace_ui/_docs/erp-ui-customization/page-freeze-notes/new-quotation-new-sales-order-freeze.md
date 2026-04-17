# Freeze Note: New Quotation and New Sales Order

Date: 2026-04-16

Status:

- Frozen for current phase
- Allowed follow-up only for high-confidence bug fixes or measured performance work

Scope:

- `New Quotation` draft page
- `New Sales Order` draft page
- shared draft runtime, shared child-page shell, shared lookup handling, and shared draft readiness behavior

Relevant implementation files:

- `C:\temp\remote_edit\erp_workspace_ui\public\js\runtime\child_page\child_page_helpers.js`
- `C:\temp\remote_edit\erp_workspace_ui\public\js\runtime\child_page\child_page_shell.js`
- `C:\temp\remote_edit\erp_workspace_ui\public\js\runtime\child_page\child_page_shell_content.js`
- `C:\temp\remote_edit\erp_workspace_ui\public\js\erp_workspace_ui_boot.js`
- `C:\temp\remote_edit\erp_workspace_ui\public\js\quotation_form.js`
- `C:\temp\remote_edit\erp_workspace_ui\public\js\sales_order_form.js`

## Freeze decision

These two draft pages are approved for the current program phase.

They are not perfect in every micro-detail, but they are now strong enough in the areas that matter for an enterprise product:

- stable draft rendering
- shared architecture instead of page-local patching
- meaningful draft guidance
- business-useful field surfacing
- usable customer, item, price list, and tax interactions
- consistent draft behavior between Quotation and Sales Order

## What is considered complete

### 1. Shared architecture

- draft gating, draft pending state, regression measurement, and performance summary are handled in shared runtime code
- Quotation and Sales Order drafts both use the same architectural pattern for preflight visibility, body readiness, and stable release
- shared-component direction is respected; this is no longer driven by one-off page-only fixes

### 2. Business workflow support

- Draft Readiness is kept because it has real business value
- it helps the user see whether the draft is commercially usable before save or downstream conversion
- Price List is surfaced directly in the draft body because it materially affects selling behavior
- Tax is demoted to optional context instead of dominating the draft experience
- Sales Order duplicate delivery-date noise is reduced by suppressing the line-level delivery date when it is redundant

### 3. UX quality

- major flashing and unstable body regressions were reduced enough to stop blocking use
- draft preparation state is now understandable and no longer feels broken
- dropdown lookup behavior for customer and item is usable again
- delete row behavior is working as expected
- draft readiness visual treatment is now present but not overly dominant

## Accepted non-blocking limitations

These are accepted for now and are not a reason to reopen the freeze immediately:

- draft main-body reveal still takes roughly 3 to 5 seconds in some runs
- minor spacing rhythm differences still exist between some section bands
- Frappe native draft boot behavior still creates some startup cost outside our direct UI layer

## What would reopen this freeze

Reopen only if one of the following happens:

- draft body regresses back to `body -> preparation -> body`
- draft fields visibly swap between wrong labels and final labels again
- customer or item lookup stops being selectable
- price list or tax context stops reflecting live ERP options
- shared runtime changes break parity between New Quotation and New Sales Order

## Next recommendation

Do not spend more time on cosmetic churn inside these two pages right now.

Recommended next path:

1. Keep these two draft pages frozen.
2. Continue the Sales Console program scope.
3. Return later only for the deferred items listed in `deferred-ui-improvements.md`.
