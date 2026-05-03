# Freeze Note: Sales Console

Date: 2026-04-16

Last implementation alignment: 2026-05-03
Final freeze decision: 2026-05-03

Status:

- Frozen after owner visual/business acceptance

Automated browser proof:

- Docker Playwright runner passed for Sales Manager and Sales User on 2026-05-02
- full live route probe passed on 2026-05-03 for Sales Manager and Sales User
- restricted Sales User routes fail safely without exposing manager-only actions
- Socket.IO realtime connects cleanly after the Caddy origin-forwarding fix
- owner visual/business acceptance is recorded on 2026-05-03

Scope:

- Sales Console inquiry workspace
- Sales Console summary cards, lifecycle cards, and navigation behavior
- shared Sales Console sidebar navigation across managed Sales Console routes
- shared operating actions across Sales Console drafts, worklists, and reports
- trust and usefulness of related-document results shown from inquiry
- productized navigation into Sales Console worklists
- productized Customers and Items entry pages
- productized Customer Detail and Item Detail pages

## Freeze decision

Sales Console is accepted as the primary sales workspace.

Final freeze marker: `sales-console-freeze-v1`

It is approved because it now does the correct job for an enterprise sales user:

- gives one entry point for inquiry
- shows business-useful summary state
- exposes real related documents
- routes the user into the correct child page

## What is accepted

### 1. Inquiry is the right focal interaction

- searching by commercial reference can surface the relevant sales chain quickly
- inquiry output is no longer just decorative status; it is intended to support real customer response
- inquiry assist answers now use a clearer four-step layout: what is happening, main risk or blocker, staff next step, and customer reply draft

### 2. Related-document truth was prioritized over visual novelty

- document flow and related-record behavior were reviewed for factual usefulness
- payment visibility was treated as commercially relevant instead of being hidden from sales by default
- the page is accepted on the basis that users can trust what it shows more than before

### 3. Navigation cards support the workflow

- navigation from console to child pages is a valid enterprise pattern here
- child-page routing and top-of-page landing were stabilized enough to stop blocking use
- operational cards now route into `sales-console-worklist/<queue-key>` instead of raw native lists
- Customers routes to `sales-console-worklist/customer-directory`
- Items routes to `sales-console-worklist/item-directory`
- the bare `sales-console-worklist` route intentionally shows a guard state because a queue key is required

### 4. Quick actions match current product intent

- primary actions are New Quotation and New Sales Order
- secondary actions are Customers and Items
- Opportunity is not part of the current Sales Console quick-action contract
- Customers and Items are accepted as directory-style worklists, not as raw ERPNext list shortcuts
- Item Detail is accepted as a productized detail route with active selling price, stock posture, and stock-by-warehouse detail

### 5. Visual quality is good enough

- the page now reads as premium and operational, not as a dashboard toy
- card sizing, counts, and section hierarchy are good enough to proceed
- shared metric cards now use the confirmed spacing and line-height pattern from the final Item Detail pass

### 6. Operating foundation is aligned in code

- Sales Console home, worklists, reports, and Quotation/Sales Order forms now share a governed sidebar navigation foundation
- New Quotation and New Sales Order now expose a productized operating action band for save, submit, print, email, assign, comment, share, and back-to-console behavior
- report pages expose `Refresh` before `Back to Sales Console` as standard top-level actions; worklists follow the same governed action taxonomy where the surface includes both actions
- restricted worklists can expose `Open Native List` as an explicit governed fallback instead of leaving the user at a dead end
- automated validation for the operating foundation passed on 2026-04-23; a short live browser smoke remains the final human checkpoint before Golden SOP promotion
- final live route probing on 2026-05-03 found no Sales Console page error states

## Accepted deferred items

- possible future workflow-chain visualization if it proves business-useful
- final copy polish for niche edge cases
- another cross-page spacing pass after the broader Sales Console surface is complete
- optional redirect from bare `/desk/sales-console-worklist` back to `/desk/sales-console` if the guard state proves confusing
- Overview first-load movement is deferred as a Desk-level visual-stability item unless the owner manual review marks it as disruptive

## Final Owner Checkpoint

Before declaring the Sales Console fully frozen, the owner should manually confirm:

- first landing on Overview does not feel unstable enough to block daily use
- the inquiry answer layout is easier to scan in real customer/order examples
- filters, date pickers, link suggestions, Apply, Reset, and Refresh behave naturally in the browser
- the current visual quality is acceptable as the first stable enterprise version

## Reopen conditions

Reopen only if:

- inquiry results become misleading or incomplete
- related documents stop being truthful or useful
- navigation from console to child pages becomes unreliable again
- Customers or Items stop routing to their productized worklist pages
- payment or return visibility regresses into non-useful presentation
