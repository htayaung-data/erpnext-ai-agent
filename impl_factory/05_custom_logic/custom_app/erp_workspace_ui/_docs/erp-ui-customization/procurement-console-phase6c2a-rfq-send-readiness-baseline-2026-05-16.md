# Procurement Console Phase 6C2A RFQ Send Readiness Protected Baseline

Date: 2026-05-16
Final accepted commit: `1f986934612bc6352979a85527c50fb050614adf`
Branch: `feature/erpnext-ui-design`

## Business Purpose

Phase 6C2A protects the first governed RFQ send-readiness surface without enabling external supplier email.

The phase lets buyers inspect supplier recipient readiness before a future governed RFQ send phase. It keeps the current supplier-facing output boundary intact: buyers can preview and download supplier-specific RFQ PDFs, but they cannot send an RFQ email from the managed workspace yet.

This baseline also closes the final acceptance repair for the managed RFQ form and RFQ Review route:

- New RFQ Supplier, Item, and Warehouse autocomplete dropdowns use the accepted below-first placement behavior.
- The RFQ Review page opened from the RFQ Directory now includes Supplier Communication controls.
- Supplier Communication remains productized and does not leak native ERPNext print/email UI.

## Scope Implemented

Implemented Phase 6C2A scope:

- RFQ Supplier Communication readiness on saved managed RFQ forms.
- RFQ Supplier Communication readiness on the RFQ Review route.
- Recipient readiness rows for RFQ suppliers.
- Missing supplier email state.
- Outgoing email availability state surfaced as controlled productized copy.
- Disabled/non-actionable `Send RFQ` state.
- Existing supplier-specific `Preview RFQ` action preserved.
- Existing supplier-specific `Download RFQ PDF` action preserved.
- RFQ Review integration for preview, PDF, supplier context, readiness, and disabled send.
- New RFQ Supplier, Item, and Warehouse autocomplete placement repair.
- Smoke and protected-gate coverage for the above behavior.

## Business Decision

Actual RFQ email setup and send is deferred.

Reason for deferral:

- Email sending can contact real suppliers.
- Sending requires an official sending identity.
- Sending requires SMTP/email account configuration.
- Email provider, domain, subscription, or payment setup may be required before reliable sending is possible.
- Active external send requires a governed send policy, audit trail, confirmation step, and owner approval.
- ERPNext submit/status behavior and supplier portal/contact side effects must remain controlled before any active send is enabled.

Phase 6C2A is therefore a readiness and review phase only. It intentionally answers whether supplier recipient information and outgoing email setup are ready, while keeping external communication blocked.

## Current UI State

Accepted current UI behavior:

- Supplier Communication appears only for saved RFQs and RFQ Review pages.
- Unsaved `/new` managed RFQ forms do not show output/readiness actions.
- Supplier Communication includes explanatory copy because send is disabled.
- The readiness-phase copy is accepted for this baseline.
- Future active-send phases should simplify this copy once sending is enabled and governed.
- `Send RFQ` is visible but disabled/non-actionable.
- `Email unavailable` or equivalent controlled outgoing-email state is shown instead of framework permission errors.
- No Frappe `Email Account` permission modal is allowed in the buyer experience.

## Accepted User Flows

Saved managed RFQ form:

1. Buyer saves a managed RFQ.
2. Saved form shows the `Supplier Communication` card.
3. Buyer selects supplier context when needed.
4. Buyer can open `Preview RFQ` in the productized preview modal.
5. Buyer can use `Download RFQ PDF` through the productized backend wrapper.
6. Buyer sees recipient readiness and outgoing email state.
7. `Send RFQ` remains disabled.

RFQ Directory and RFQ Review:

1. Buyer opens RFQ Directory.
2. Buyer opens a saved RFQ review page at `/desk/procurement-console-rfq-review/<rfq-name>`.
3. RFQ Review shows `Supplier Communication`.
4. Buyer can preview supplier-specific RFQ output.
5. Buyer can download supplier-specific RFQ PDF.
6. Buyer sees recipient readiness and disabled send state.
7. No duplicate Supplier Communication section appears after repeated navigation.

New managed RFQ form autocomplete:

- Supplier autocomplete opens below the active input when there is usable space.
- Item autocomplete opens below the active input when there is usable space.
- Warehouse autocomplete opens below the active input when there is usable space.
- Dropdowns cap height and scroll when constrained.
- Dropdowns flip upward only when below placement is genuinely unavailable.
- Dropdowns do not overlap the toolbar/header when below placement is available.

## Explicit Non-Scope

Phase 6C2A does not implement:

- Actual RFQ send/email.
- Communication record creation.
- Email Queue creation.
- Contact creation.
- User creation.
- Supplier portal invitation or supplier portal flow.
- ERPNext RFQ submit.
- Approval/rejection workflow.
- Ready-to-send mutation.
- RFQ-to-Supplier Quotation conversion.
- Supplier Quotation-to-Purchase Order conversion.
- Purchase Request or Material Request-to-Purchase Order conversion.
- Receive / Purchase Receipt.
- Bill / Purchase Invoice.
- Payment.
- Item Price mutation.
- Default Supplier mutation.
- Supplier or Item master-data mutation.
- Purchase Order send.
- Email account setup.
- Broad Procurement redesign.
- Sales Console runtime changes.

## Productized Output And Native Leakage Boundary

Protected rules:

- RFQ preview and PDF remain productized actions.
- Preview must not expose native embedded ERPNext `Print` or `Get PDF` controls.
- PDF download must go through the managed backend wrapper.
- Native ERPNext email composer must not open from Phase 6C2A UI.
- Native supplier portal invite actions must not be exposed.
- Framework permission errors, including Email Account permission dialogs, must not surface to buyers.
- Direct native email/send is not accepted as a primary UX.

## Backend And Safety Contract

Backend-owned behavior protected by this baseline:

- RFQ readiness context is read server-side from the saved RFQ.
- Supplier rows come from the RFQ document, not client payload.
- Outgoing email availability is represented as controlled readiness state.
- Backend handles unavailable or permission-limited email account lookups safely.
- Purchase Manager and Purchase User access follows existing Procurement/ERPNext permission rules.
- Sales roles and Guest remain denied by existing access rules.
- Client code does not decide send eligibility.
- `can_send` remains false in Phase 6C2A.
- No mutation occurs while building readiness context.

## Evidence

Accepted implementation commit:

- `1f986934612bc6352979a85527c50fb050614adf`

Focused Phase 6C2A live smoke:

- `/tmp/procurement-phase6c2a-repair-live-final-20260516T135953Z/procurement-phase6c2a`

Focused Sales worklist rerun:

- `/tmp/sales-worklists-focused-phase6c2a-20260516T155859Z`

Sales freeze:

- `/tmp/sales-freeze-phase6c2a-rerun-20260516T160037Z`

Full protected workspace gate:

- `/tmp/protected-workspaces-phase6c2a-final-pass-20260516T160517Z`

Live-aligned runtime hashes:

- `document_reviews.py`: `1d0ecae156e8a528a4ca41afd88ae7b0d7b32ad748ce0ad5a5969cd3afc95aa4`
- `procurement_console_review_page.js`: `a8bec57cfe203d591009b230b2d4475882fbf61756d35488954d9195acf94e8a`
- `procurement_console_rfq_form.js`: `97dbb87bf313a1f6fce023905da40601199868224ab37e533af150f563909a22`
- `workspace_governance_manifest.py`: `e5f9febe7083e39e318676d7253e60cfebd3d2ebfd5bd322af43ece76b9dfa40`

Acceptance facts:

- Owner manual review accepted.
- Focused Phase 6C2A live smoke passed.
- Focused Sales worklist rerun passed.
- Sales freeze passed.
- Full protected workspace gate passed.
- Source/live hashes matched for synced runtime files.
- No Sales runtime change was made.

## Manual Review Checklist

Owner manual review accepted these checks:

- New RFQ Supplier autocomplete dropdown placement.
- New RFQ Item autocomplete dropdown placement.
- New RFQ Warehouse autocomplete dropdown placement.
- RFQ Review page from RFQ Directory shows Supplier Communication.
- `Preview RFQ` opens productized preview.
- `Download RFQ PDF` works and remains supplier-specific.
- `Send RFQ` is visible but disabled.
- No native email composer appears.
- No embedded native print controls appear.
- No Frappe permission modal appears.

## Future Protection Rules

Any future work touching RFQ Supplier Communication, RFQ output, RFQ readiness, RFQ Review, managed RFQ autocomplete, or shared Procurement route/runtime behavior must run:

- Focused affected RFQ smoke.
- Focused Phase 6C2A smoke or successor coverage.
- Full protected workspace gate.
- Sales freeze if shared runtime changes are involved.
- Manual review of RFQ Review Supplier Communication and New RFQ autocomplete placement.

Any active RFQ send/email phase must be separately designed and owner-approved before implementation.

## Next Recommended Design Task

The next recommended task is design-only:

`Phase 6C2B RFQ Governed Send Design`

That design should decide official sending identity, email configuration readiness, confirmation flow, audit trail, status policy, supplier recipient rules, failure/retry handling, and whether ERPNext submit is required before active RFQ send.
