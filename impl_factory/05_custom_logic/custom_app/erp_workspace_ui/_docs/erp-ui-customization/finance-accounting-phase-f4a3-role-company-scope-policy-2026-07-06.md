# Finance & Accounting F4A3 Role + Company Scope Policy - 2026-07-06

Status: policy and governance only. This document does not implement Finance runtime data, create users, create roles, change permissions, call reports, expose native routes, live-align, restart, reload metadata, migrate, commit, or push.

## Decision

F4A3 defines the role and allowed-company authorization model that must gate future Finance amount visibility. F4A2 approved manager-level company-scoped amount totals in principle; F4A3 defines who may qualify for that visibility and how company scope must be resolved before F4B can load any AR/AP/cash amount data.

Accepted policy direction:

- `Accounts Manager` is the first accepted manager-level Finance visibility role.
- `finance.lead@meet.com` is the current live manager candidate because it has `Accounts Manager`.
- `Finance Lead Approver` may be used later for custom review or workflow posture, but it is not enough by itself for Finance amount visibility unless Owner/Main Control explicitly approves it.
- `Accounts User` is the accepted normal finance user role for limited posture/count visibility.
- `Auditor` exists but needs explicit audit/company scope before Finance data visibility is granted.
- `Executive Approver` is not Finance data access by itself.
- `System Manager` is admin/shell authority only by default and is not automatic Finance data authority.
- Non-finance users remain restricted.
- The current site has one company, `Mingalar Mobile Distribution Co., Ltd.`, with default currency `MMK`.
- Future F4B may use a strict single-company fallback only on the current one-company site and only after role, source permission, company resolver, and Owner/Main Control gates pass.

## Current Live Role Mapping

The current role audit is accepted as policy input only. No users or roles are created or changed by F4A3.

| User / role group | Current observed roles | F4A3 policy decision |
| --- | --- | --- |
| `finance.lead@meet.com` | Accounts Manager, Finance Lead Approver, Desk User, Employee | Current live manager candidate for future manager-level amount visibility because it has `Accounts Manager`. |
| `accounts.ygn.01@meet.com` | Accounts User, Desk User | Normal finance user candidate for shell, Tier 0, and future limited count/posture visibility. |
| `accounts.mdy.01@meet.com` | Accounts User, Desk User, Employee | Normal finance user candidate for shell, Tier 0, and future limited count/posture visibility. |
| `cashier.ygn.01@meet.com` | Accounts User, Desk User, Employee | Normal finance user candidate for shell, Tier 0, and future limited count/posture visibility; cashier identity does not imply payment execution in the custom workspace. |
| `general.manager@meet.com` | Executive Approver, Purchase Manager, Sales Manager, Stock Manager | Executive/business manager candidate only. Not Finance data access until explicit Owner/Executive Finance mapping is accepted. |
| `warehouse.manager@meet.com` | Stock/Delivery roles only | Non-finance for Finance workspace data; restricted from Finance data. |
| `Administrator` | Broad admin/finance authority | Admin/shell only by default in the custom Finance workspace unless explicit finance test/owner scope is used. |
| `htayaung.data@gmail.com` | Broad admin/finance authority | Admin/owner-like broad account; must be treated as explicit test/owner scope, not a normal role policy precedent. |

## Role Mapping Policy

| Role | Shell access | Future count visibility | Future amount-total visibility | Customer/invoice visibility | Execution authority | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Accounts Manager | Yes. | Yes after F4B gates. | Yes in principle after F4B gates. | Future separate approval. | No in custom workspace. | Primary manager-level Finance visibility role. |
| Finance Lead Approver | Future shell/review candidate only. | Not enough by itself. | Not enough by itself. | No. | No. | May support future custom review records if paired with approved Finance visibility role. |
| Accounts User | Yes. | Future limited count/posture visibility. | Not approved by default; future optional only with Owner-approved limited amount policy. | Blocked first cycle. | No. | Normal finance users should not receive manager amount totals by default. |
| Auditor | Future yes if audit scope accepted. | Future read-only if approved. | Future read-only if company/audit scope approved. | Future separate approval. | No. | No dedicated normal auditor test user is confirmed. |
| Executive Approver | Not Finance data access by itself. | No by default. | No by default. | No by default. | No. | `general.manager@meet.com` needs explicit Owner/Executive Finance mapping before Finance data visibility. |
| System Manager | Shell/admin only by default. | No Finance data by default. | No Finance amounts by default. | No by default. | No in custom workspace. | Must also have an approved Finance role and company scope to see Finance data. |
| Owner / Executive custom mapping | Future explicit mapping required. | Future summary counts if accepted. | Future executive totals if accepted. | Future separate approval. | No in custom workspace. | Business owner decision, not inferred from System Manager or Executive Approver alone. |
| Non-finance roles | Restricted. | No. | No. | No. | No. | Includes Warehouse, Sales, Procurement, Stock, Delivery, and other non-Finance users. |

Role eligibility is necessary but never sufficient. Future Finance data visibility requires role eligibility, allowed-company scope, source read permission, field allowlist, currency/amount policy, and exact response-key tests.

## Company Scope Decision

One enabled company is currently known:

- Company: `Mingalar Mobile Distribution Co., Ltd.`
- Default currency: `MMK`

Policy:

- Default company can be used only as a preferred filter or display hint. It is not authorization.
- Allowed company must be resolved by an explicit backend resolver before Finance counts, aging buckets, amount totals, cash indicators, AP posture, or any financial rows are returned.
- The resolver may use Company User Permission where present.
- The resolver may use an explicitly accepted single-company fallback only when the site has exactly one enabled company.
- The resolver must require role eligibility and source permission checks in addition to company scope.
- Branch permissions are not enough for Finance company authorization unless a later policy maps Branch to Company with tests.
- Multi-company sites require explicit selected company and must not default to all-company totals.

Resolver rejection cases:

- no enabled company is available;
- requested company is outside allowed scope;
- default company is not allowed;
- role is eligible but source read permission is denied;
- System Manager has no approved Finance role;
- user has only non-finance roles;
- multi-company user has not selected an approved company;
- company/currency context is ambiguous.

## Single-Company Fallback Policy

Future F4B may allow a safe single-company fallback for the current one-company site only when all of these conditions are true:

- exactly one enabled company exists;
- the company is `Mingalar Mobile Distribution Co., Ltd.` or the backend confirms the same single enabled company dynamically;
- the user has an approved Finance role for the requested visibility tier;
- source read permission is approved and tested for the selected source;
- no multi-company ambiguity exists;
- field allowlist and source-field/query allowlist are enforced;
- currency policy is accepted for `MMK`;
- the response marks company scope source as `single_company_site_fallback`;
- the response includes explicit no-effect flags;
- tests prove the fallback is disabled when more than one enabled company exists.

This fallback must not be used on multi-company sites, and it must not become a substitute for Company User Permission once a clean Finance company-scope model exists.

## Currency Policy For Current Site

`MMK` is the only current company default currency in scope for this policy.

Future F4B may display manager-level AR aging amount totals in `MMK` only after Owner/Main Control accepts F4A3 and F4B source/read policy. First-cycle amount display must be limited to company-scoped aggregate totals, not customer balances or invoice rows.

Currency rules:

- no mixed-currency totals in the first cycle;
- no conversion, revaluation, base/party currency comparison, or foreign-currency presentation in the first cycle;
- if multiple company currencies, party currencies, or source currencies appear later, amount totals must return unavailable until policy is expanded;
- amount labels must identify the `MMK` basis without exposing native report internals;
- no customer-level or invoice-level amount fields are approved by F4A3.

## Native ERPNext Role Risk

ERPNext native `Accounts User` and `Accounts Manager` roles may already have broad permissions for accounting and commercial DocTypes such as Sales Invoice, Purchase Invoice, Payment Entry, Journal Entry, Bank Transaction, Payment Reconciliation, Customer, Supplier, Account, and reports.

Custom Finance workspace policy is stricter than native Desk capability:

- workspace visibility is not execution authority;
- native ERPNext roles must not automatically expose native routes, reports, Form/List views, exports, print views, or lifecycle actions in the custom workspace;
- F4B must block posting, payment, reconciliation, write-off, tax, close, customer communication, and native execution even if the user could perform some action elsewhere in ERPNext;
- no custom workspace UI should imply that native role permissions are being delegated or approved.

## F4B Readiness Criteria

F4B can begin only after Owner/Main Control accepts F4A3 and agrees to all of the following:

- use `Accounts Manager` as the first manager amount-visibility role;
- treat `finance.lead@meet.com` as the current live manager candidate because it has `Accounts Manager`;
- use `Accounts User` for limited normal finance visibility, with counts/posture first;
- keep `System Manager` out of Finance data unless the user also has an approved Finance role and allowed company scope;
- treat `Executive Approver` as not enough for Finance data access without explicit Owner/Executive mapping;
- allow the single-company fallback for the current one-company site under the strict conditions above;
- display `MMK` amount totals for manager-level AR aging only if source, read, amount, and currency policy tests pass;
- keep customer names, customer balances, invoice identifiers, due dates, statuses, line items, and invoice rows blocked;
- keep native routes, reports, exports, print, and execution controls blocked.

F4B remains not ready until these decisions are accepted and translated into focused tests.

## Future F4B Tests Required

F4B tests must cover at minimum:

- `finance.lead@meet.com` / Accounts Manager with single-company fallback: allowed for approved manager posture and, if currency policy passes, aggregate `MMK` amount totals;
- `accounts.ygn.01@meet.com` / Accounts User: count-only or limited posture according to accepted F4B policy, no manager amount totals by default;
- `accounts.mdy.01@meet.com` / Accounts User: same limited normal finance visibility behavior;
- `cashier.ygn.01@meet.com` / Accounts User: no payment execution and no cashier-specific escalation;
- Auditor role: read-only visibility only if explicitly approved; otherwise restricted or unavailable;
- System Manager only: no Finance data;
- `general.manager@meet.com` / Executive Approver without Accounts role: no Finance data until explicit Owner/Executive mapping;
- `warehouse.manager@meet.com` and other Warehouse/Sales/Procurement users: restricted;
- no enabled company: restricted or unavailable;
- requested company outside allowed scope: rejected;
- default company not allowed: rejected;
- multi-company with no explicit selected company: unavailable;
- multi-company all-company aggregate request: rejected unless separately approved;
- currency mismatch or multi-currency source: unavailable;
- source read permission denied: restricted or unavailable;
- no native route/report/export/print strings in touched source;
- no posting/payment/reconciliation/write-off/tax/close/customer communication behavior;
- exact response keys and explicit no-effect flags.

## Boundaries

F4A3 does not approve or implement:

- AR/AP/cash runtime data in this phase;
- user creation, role creation, permission mutation, or User Permission records;
- Sales Invoice lifecycle;
- Purchase Invoice lifecycle;
- Payment Entry lifecycle;
- Journal Entry lifecycle;
- GL Entry mutation;
- Bank Transaction mutation or bank reconciliation;
- Payment Reconciliation mutation;
- write-off, adjustment, credit note, debit note, allocation, or unallocation;
- tax filing, Period Closing Voucher, close submission, or compliance submission;
- email, notification, portal, customer statements, dunning, Communication, Email Queue, Payment Request, or external customer/supplier action;
- native ERPNext route, report, export, download, print, Form, List, Query Report, Script Report, or Desk execution path;
- live alignment, restart, metadata reload, migration, protected gate, commit, or push.

## Boundary Confirmation

F4A3 implements no Finance runtime data. It creates no users or roles. It approves no accounting execution, posting, payment, reconciliation, write-off, Sales Invoice lifecycle behavior, Purchase Invoice lifecycle behavior, Payment Entry lifecycle behavior, Journal Entry lifecycle behavior, GL mutation, bank reconciliation mutation, native Finance route/report/export behavior, customer notification, email, portal behavior, live alignment, restart, metadata reload, protected gate, commit, or push.
