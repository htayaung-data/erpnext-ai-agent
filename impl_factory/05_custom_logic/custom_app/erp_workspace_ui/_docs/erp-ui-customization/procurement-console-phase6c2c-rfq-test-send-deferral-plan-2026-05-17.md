# Procurement Console Phase 6C2C RFQ Test Send Deferral Plan

Date: 2026-05-17
Superseded implementation commit: `30e4d8902315becdf58099a460378e450175df56` introduced controlled RFQ test-send runtime. The corrective commit containing this note removes that runtime.
Protected baseline before this deferral: Phase 6C2A RFQ Send Readiness at `9450691b131489c5ef41aa886da8d78ed972e859`
Decision scope: corrective deferral. This note does not enable supplier email send, and the current protected runtime state must contain no active send endpoint or SMTP send path.

## Corrective Runtime Status

A controlled RFQ test-send implementation was attempted in `30e4d8902315becdf58099a460378e450175df56`. That implementation added SMTP environment handling, a backend test-send path, frontend confirmation hooks, controlled-email governance entries, and a Phase 6C2C send smoke.

That runtime is not accepted because the approved business decision is to defer RFQ email/send. The corrective commit containing this document update removes the attempted test-send runtime from source and must be live-aligned before Phase 6C2C can be considered cleanly deferred.

Current protected runtime expectation after the corrective commit:

- No backend RFQ test-send method.
- No SMTP password/configuration send path in source.
- No Python SMTP send runtime in the document output module.
- No enabled RFQ test-send confirmation flow.
- No Phase 6C2C send smoke or package script.
- No controlled email test governance endpoint.
- Supplier Communication, Preview RFQ, Download RFQ PDF, recipient readiness, and disabled Send RFQ remain protected.

## Decision

Defer active RFQ email/send implementation until the ERP product is closer to production readiness or until the owner explicitly approves email infrastructure setup.

The current system should remain in a safe readiness posture:

- Supplier-specific RFQ Preview remains available.
- Supplier-specific RFQ PDF Download remains available.
- Recipient readiness remains visible.
- Send RFQ remains disabled/non-actionable; no test/demo email transport is active in the protected runtime.
- No production supplier emails should be sent from the ERP at this stage.

This deferral is intentional. It is not a product failure and not a reason to buy more infrastructure immediately.

## Why Active Send Is Deferred

RFQ email send is an external supplier communication. Enabling it too early creates operational and legal risk because it can contact real suppliers, distribute buyer documents, and create audit expectations before the full Procurement workflow is stable.

Current infrastructure also does not support the first test-send path cleanly:

- The ERP is hosted on DigitalOcean Droplets. DigitalOcean blocks outbound SMTP ports `25`, `465`, and `587` by default on Droplets, including Reserved IP traffic. DigitalOcean recommends a third-party email service rather than direct SMTP from Droplets.
- Google Workspace SMTP over port `587` is therefore not a reliable path from the current ERP host.
- Resend would avoid SMTP by using an HTTPS API, but its normal domain verification requires DNS records for a sending/return-path subdomain such as `send.example.com`.
- The observed Resend/Wix setup screen reports that Wix does not support subdomain MX records for this verification path. Resend's own documentation explains that it uses an MX record on `send.example.com` for return-path/bounce handling.
- Moving DNS away from Wix or buying a separate sending domain is possible, but it is not required until the ERP is nearer to supplier-facing UAT or go-live.

Because of these constraints, the safest business decision is to keep the RFQ send UI in readiness/disabled mode and revisit email infrastructure later.

## Current Accepted User Experience

The protected RFQ communication surface remains:

- Saved managed RFQ form shows Supplier Communication.
- RFQ Review page from the RFQ Directory shows Supplier Communication.
- Preview RFQ opens productized preview.
- Download RFQ PDF uses the controlled backend wrapper and stays supplier-specific.
- Recipient readiness shows supplier/contact/email availability.
- Email availability is displayed as a productized state, not a raw framework permission error.
- Send RFQ is visible but disabled/non-actionable; a future approved phase is required before any safe transport is added.
- New RFQ Supplier, Item, and Warehouse autocomplete dropdowns use the accepted below-first placement behavior.

## Current Non-Scope

The following remain explicitly out of scope:

- Actual RFQ email send to suppliers.
- Production email provider configuration.
- SMTP password or API key storage.
- ERPNext native RFQ send exposure.
- Native email composer exposure.
- Contact creation.
- User creation.
- Supplier portal invitation.
- Communication creation for real sends.
- Email Queue creation for real sends.
- ERPNext RFQ submit.
- RFQ-to-Supplier Quotation conversion.
- Purchase Order creation.
- PO email/send.
- Receive, bill, payment, or other lifecycle actions.
- Item Price or Default Supplier mutation.

## Recommended Timing

Do not buy a new domain or paid email sending service solely for the current implementation stage unless the owner wants real email delivery testing immediately.

Recommended trigger to reopen RFQ send implementation:

1. The managed Procurement workflow is stable enough for supplier-facing UAT, or the owner approves test emails as a formal milestone.
2. The owner chooses a long-term email sending architecture.
3. Sender identity, DNS, audit, and permission policy are approved.
4. A controlled test recipient is available.
5. The implementation phase includes smoke tests proving no native send leakage and no accidental supplier contact.

## Future Email Architecture Options

### Option A: Wait Until Production Email Setup

Use this option if there is no immediate need to send real RFQ emails during implementation.

Recommended setup later:

- Company sender such as `procurement@myanmarexcel.com`, `buying@myanmarexcel.com`, or `sourcing@myanmarexcel.com`.
- SPF, DKIM, and DMARC configured.
- Clear reply-to mailbox ownership.
- Provider selected before implementation.
- Owner-approved send confirmation and audit trail.

This is the recommended path now.

### Option B: Move DNS Away From Wix Later

Use this option if the owner wants to use `myanmarexcel.com` directly with providers requiring subdomain MX records.

Expected work:

- Move DNS management to a provider that supports subdomain MX records, such as Cloudflare or another full DNS host.
- Preserve existing Google Workspace MX records during migration.
- Add sending-provider TXT/CNAME/MX records as required.
- Validate mail delivery before enabling ERP send.

This should be scheduled carefully because DNS migration can affect website and email availability.

### Option C: Buy A Separate Sending/Test Domain Later

Use this option if the owner wants clean separation from the main company domain.

Example pattern:

- Buy a low-cost domain dedicated to ERP sending or testing.
- Manage DNS at a provider that supports all verification records.
- Verify it in an email API provider.
- Send test RFQs from a clearly labeled sender.

This avoids touching the main Wix-managed domain, but it adds cost and another asset to maintain.

### Option D: Use An Email API Provider Later

Use this option if the ERP remains hosted on DigitalOcean and direct SMTP is blocked.

Possible providers:

- Resend, if DNS verification can be satisfied.
- Postmark.
- SendGrid.
- Mailgun.
- Brevo.
- Amazon SES.

Implementation should use HTTPS API calls where possible so DigitalOcean SMTP port restrictions do not block delivery. Any API key must be provided through runtime environment variables or a secrets manager, never source control.

## Future Phase Recommendation

When the owner decides to reopen RFQ send, create a new governed phase rather than modifying Phase 6C2A informally.

Suggested future phase: `Phase 6C2C2 RFQ Governed Email Send Provider Integration`, only after owner approval reopens send.

Required scope:

- Select provider and sender identity.
- Validate DNS and deliverability readiness.
- Keep Send disabled until provider readiness is green.
- Send only to an explicit selected supplier or approved test override.
- Show confirmation modal before email leaves the ERP.
- Attach supplier-specific RFQ PDF.
- Record audit trail after successful send.
- Provide controlled failure states for provider/API errors.
- Confirm no secret leakage in logs, screenshots, artifacts, or repo.

Required exclusions:

- No mass send by default.
- No native ERPNext RFQ send.
- No supplier portal user creation.
- No Contact/User creation unless owner approves a separate phase.
- No RFQ submit unless submit governance is separately approved.
- No conversions or PO lifecycle actions.

## Protection Requirements For Reopening Send

Before any future active-send phase can be accepted, run:

- Source validation: compileall, unit discovery, JS syntax checks, and diff whitespace checks.
- Focused RFQ send smoke in disabled/no-provider mode.
- Focused RFQ send smoke in test-provider mode using an owner-approved test recipient only.
- Screenshot review of Supplier Communication on saved managed RFQ and RFQ Review.
- Verification that no native email composer appears.
- Verification that no native print controls appear in preview.
- Verification that no supplier portal, Contact, or User records are created.
- Sales freeze protection.
- Full protected workspace gate.

Owner manual review must confirm receipt of the test email before active-send implementation can be closed.

## Security Rules

Future email credentials must follow these rules:

- Do not commit passwords, API keys, app passwords, OAuth secrets, or tokens.
- Do not place secrets in documentation, screenshots, smoke artifacts, or issue text.
- Do not print secrets in terminal output.
- Prefer runtime environment variables or a secrets manager.
- If a provider requires storing credentials in ERPNext Email Account, that must be an explicit owner-approved live configuration action, not an automatic code path.

## References

- DigitalOcean SMTP blocking: https://docs.digitalocean.com/support/why-is-smtp-blocked/
- Resend domain and DNS verification: https://resend.com/docs/dashboard/domains/introduction
- Resend MX/return-path explanation: https://resend.com/docs/knowledge-base/how-do-i-avoid-conflicting-with-my-mx-records
- Wix MX record management: https://support.wix.com/en/article/adding-or-updating-mx-records-in-your-wix-account
