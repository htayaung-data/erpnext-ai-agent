# Sales Console Enterprise Readiness Audit: SERA-2 Security And Permissions

Date: 2026-04-28
Status: Pass for Sales Manager/Sales User gate with manual save-persistence check still optional
Audit phase: `SERA-2` Security, Permission, And Data Mutation Safety
Depends on:

1. `enterprise-shared-ui-component-standard-v1.md`
2. `enterprise-shared-ui-component-implementation-contract-v1.md`
3. `sales-console-enterprise-readiness-sera-0-baseline.md`
4. `sales-console-enterprise-readiness-sera-1-route-ownership.md`
5. `sales-console-enterprise-readiness-standards-hardening-addendum.md`

## 1. Purpose

This note records the Sales Console security and permission audit.

The goal is to prove that the Sales Console is safe enough to continue as the reference workspace before it is copied into other ERP workspaces.

This phase checks:

1. whitelisted backend methods
2. read APIs and record visibility
3. Customer create/edit mutation safety
4. allowed-field contracts
5. native ERP mutation boundaries
6. controlled permission elevations
7. restricted-state behavior
8. remaining role and browser verification

## 2. SERA-2 Decision

SERA-2 decision:

`Conditional Pass with security hardening and required role verification`

Reason:

1. Guest access is rejected on all primary whitelisted Sales Console methods.
2. Customer create/edit is server-gated by Sales Manager role variant plus native Customer create/write permission.
3. Customer create/edit accepts only a small allowlist of sales profile fields.
4. Customer save uses native Customer `insert` and `save` with `ignore_permissions=False`.
5. Direct customer inquiry record loading was hardened to permission-aware reads.
6. Customer and item directories were hardened to use permission-aware document reads before enrichment.
7. Payment Entry detail access is guarded before payment settlement references are resolved.
8. No custom backend delete, submit, cancel, or workflow bypass was found in the Sales Console audit scope.
9. A controlled Contact permission elevation remains intentionally present; the live Sales Manager/Sales User role gate is verified, while an actual contact-save mutation can remain a manual freeze check.
10. Authenticated browser and role-matrix verification is complete for the Sales Manager and Sales User accounts used in the 2026-05-01 live smoke pass.

Important limitation:

This is a static code audit plus targeted code hardening. It did not execute live authenticated role tests because the shell does not currently provide a reusable authenticated browser session.

## 3. Security Principle

Sales Console security must follow this order:

1. authenticate first
2. resolve role and Sales Console scope
3. read only permission-visible parent records
4. enrich only records already proven visible
5. mutate only through explicit server-side allowlists
6. delegate transactional lifecycle actions to native ERPNext permissions
7. document every intentional permission elevation

The enterprise rule is:

`Permission first. Enrichment second. Mutation last.`

No future workspace should copy a page pattern that reads parent business records with permission-bypassing APIs before proving visibility.

## 4. Whitelisted Method Inventory

### 4.1 Sales Console Service Methods

Source:

`erp_workspace_ui/sales_console/service.py`

| Method | Type | Security decision |
| --- | --- | --- |
| `get_sales_console_bootstrap` | read/context | Accept. Guest rejected, scope derived from current user. |
| `get_sales_console_sidebar_context` | read/context | Accept. Guest rejected, sidebar context is user-scoped. |
| `search_sales_console_workspace` | read/search | Accept. Uses Sales Console scope and productized targets. |
| `resolve_customer_inquiry` | read/inquiry | Accept after hardening. Direct doctype/name reads now use permission-aware loading. |
| `suggest_customer_inquiry` | read/suggestion | Accept. Suggestions resolve through visible records. |
| `generate_customer_inquiry_assist` | read/AI assist | Conditional accept. It is read-only and falls back safely, but no new AI expansion should happen until final UI freeze. |

### 4.2 Sales Console Worklist Methods

Source:

`erp_workspace_ui/sales_console/worklist.py`

| Method | Type | Security decision |
| --- | --- | --- |
| `get_sales_console_worklist_context` | read/worklist | Accept after hardening. Customer and item parent reads now use permission-aware APIs. |
| `save_sales_console_customer_profile` | controlled mutation | Conditional accept. Server role, permission, scope, and field allowlist are enforced. Contact elevation must be role-tested. |

### 4.3 Sales Console Report Methods

Source:

`erp_workspace_ui/sales_console/report.py`

| Method | Type | Security decision |
| --- | --- | --- |
| `get_sales_console_report_context` | read/report | Accept for SERA-2. Report builders use Sales Console scope and native report execution where applicable. SERA-4 should review each report family in more detail. |

### 4.4 Managed Form Context APIs

Source:

`erp_workspace_ui/api.py`

| Method | Type | Security decision |
| --- | --- | --- |
| `get_sales_order_page_context` | read/form context | Accept. Native document read permission checked before response. |
| `get_quotation_page_context` | read/form context | Accept. Native document read permission checked before response. |
| `get_delivery_note_page_context` | read/form context | Accept. Native document read permission checked before response. |
| `get_sales_invoice_page_context` | read/form context | Accept after payment guard. Payment Entry detail is not resolved unless Payment Entry read is allowed. |

## 5. Mutation Surface Inventory

### 5.1 Customer Create/Edit

Primary mutation:

`save_sales_console_customer_profile`

Server-side gate:

1. rejects `Guest`
2. normalizes payload server-side
3. resolves current Sales Console context and scope server-side
4. only accepts `new` or `edit` mode
5. requires `role_variant == sales_manager`
6. requires native `Customer` create permission for new records
7. requires native `Customer` write permission for existing records
8. existing edit requires the Customer to be visible in the current Sales Console scope
9. writes Customer using `ignore_permissions=False`
10. reloads saved Customer and returns saved truth to the UI

Allowed Customer profile fields:

1. `customer_name`
2. `customer_group`
3. `territory`
4. `mobile_no`
5. `email_id`

Blocked by omission:

1. credit limit
2. payment terms
3. tax settings
4. account controls
5. workflow state
6. owner
7. credit controller fields
8. delete and disable controls

Decision:

`Conditional Pass`

Reason:

The Customer mutation path is narrow and server-authorized. The Sales User and Sales Manager role gate was verified on 2026-05-01 without creating or updating business records.

### 5.2 Contact Synchronization

Customer phone and email are synchronized to the primary Contact.

Controlled elevation:

1. `Contact.save(ignore_permissions=True)`
2. `Contact.insert(ignore_permissions=True)`

Why this exists:

Sales Console lets a Sales Manager keep customer contact details current without exposing the full native Contact form.

Risk:

This is a deliberate permission elevation. If a Sales Manager has Customer write permission but no Contact write permission, Sales Console can still update the customer's primary Contact phone and email.

Risk controls already present:

1. Sales Manager role gate happens before the helper runs.
2. Customer create/write permission is required before the helper runs.
3. Existing Customer edit must pass Sales Console customer visibility scope first.
4. Only normalized phone and email values reach the Contact helper.
5. The helper does not expose arbitrary Contact fields.
6. Code comments now document the controlled elevation.

Decision:

`Conditional Pass`

Required role test:

Confirm that a Sales Manager can update intended customer contact fields and that a Sales User cannot call the save API directly.

### 5.3 Native ERPNext Lifecycle Actions

Native lifecycle actions observed from custom UI:

1. new Quotation
2. new Sales Order
3. ToDo follow-up creation
4. form Save
5. form Submit where native form allows it
6. Print
7. Email
8. Assign
9. Share
10. Attachment
11. Tags

Decision:

`Accept as managed native ERP actions`

Reason:

These actions are not custom backend mutations in Sales Console. They delegate to native ERPNext form and permission behavior.

Boundary:

Sales Console may present or simplify these actions, but it must not bypass native submit, cancel, delete, email, print, assignment, or share permissions.

### 5.4 Unsafe Actions Not Found

No custom Sales Console backend method was found that directly performs:

1. delete
2. submit
3. cancel
4. workflow approval
5. role assignment
6. permission changes
7. credit limit changes
8. payment term changes
9. tax setting changes

Decision:

`Accept`

## 6. Read Safety Hardening Completed

### 6.1 Direct Inquiry Record Loading

Issue found:

Direct customer inquiry could receive `doctype + name`. The original pattern used raw record lookup for the anchor document and customer summary.

Risk:

A user who knew a document ID could potentially receive record context based on doctype-level read permission rather than record-level visibility.

Hardening applied:

1. `_load_anchor_document` now uses permission-aware `frappe.get_list`.
2. `_load_customer_summary` now uses permission-aware `frappe.get_list`.

Decision:

`Fixed`

### 6.2 Customer Directory And Customer Detail

Issue found:

Customer directory, customer detail, customer filters, and recent activity areas used permission-bypassing parent reads in some places.

Risk:

Customer rows or activity could be visible outside native record permissions if scope filters were not enough.

Hardening applied:

1. Customer directory parent rows now use `frappe.get_list`.
2. Customer detail parent row now uses `frappe.get_list`.
3. Customer territory/group filter options now use `frappe.get_list`.
4. Customer recent activity rows now use `frappe.get_list`.
5. Customer outstanding exposure now uses permission-aware Sales Invoice aggregation.
6. Customer page now returns a restricted payload if Customer read permission is absent.

Decision:

`Fixed`

### 6.3 Item Directory

Issue found:

Item directory parent rows were produced by a raw SQL Item query joined with Bin stock.

Risk:

The stock signal was useful, but Item identity should be proven visible before warehouse stock enrichment is applied.

Hardening applied:

1. Item parent rows now use permission-aware `frappe.get_list`.
2. Item group filter options now use permission-aware `frappe.get_list`.
3. Stock totals and warehouse quantities are calculated only after visible Item rows are resolved.

Decision:

`Fixed`

### 6.4 Payment Entry Settlement Details

Issue found:

Sales Invoice context already checked Payment Entry read for reference count, but Payment Entry detail resolution should also guard before child reference lookup.

Hardening applied:

1. `_linked_payment_entries_for_invoice` now returns no payment details unless Payment Entry read permission is available.
2. `_linked_payment_entry_reference_count` remains guarded by Payment Entry read permission.

Decision:

`Fixed`

## 7. Accepted Controlled Enrichment

Some Sales Console values are derived from child tables or linked records after a visible parent record is established.

Accepted controlled enrichments:

1. Customer Credit Limit child rows for visible Customers
2. Contact phone and email for visible Customers
3. Bin stock quantities for visible Items
4. transaction child tables used to discover linked parent documents

Enterprise rule:

These enrichments are acceptable only when the parent business record has already been proven visible.

Future workspace rule:

Never query child-table or linked-record data first and then decide whether the parent is visible. Parent visibility must come first.

## 8. Role Matrix

| Role family | Read Sales Console | Create Customer | Edit Customer profile | Delete Customer | Credit/payment/tax controls |
| --- | --- | --- | --- | --- | --- |
| Sales User | Yes, if native read permissions allow | No | No | No | No |
| Key Account Sales | Yes, assigned-account scope | No by Sales Console rule | No by Sales Console rule | No | No |
| Showroom Sales | Yes, showroom/branch scope | No by Sales Console rule | No by Sales Console rule | No | No |
| Sales Manager | Yes, team scope | Yes, only with Customer create permission | Yes, only with Customer write permission | No | No |
| Executive/GM | Review scope where configured | Not exposed in Sales Console V1 | Not exposed in Sales Console V1 unless role policy changes | No | No |
| Admin/Finance | Native ERP control | Native ERP control | Native ERP control | Native ERP control | Native ERP control |

Decision:

Sales Console V1 should keep Customer C/U narrow and should not expose Customer delete.

## 9. Server-Side Tamper Resistance

Direct API tampering expectations:

| Attempt | Expected result |
| --- | --- |
| Guest calls any primary Sales Console method | Permission error |
| Sales User calls Customer save API | Permission error |
| Sales Manager without Customer create calls new Customer API | Permission error |
| Sales Manager without Customer write calls edit Customer API | Permission error |
| Edit Customer outside current scope | Permission error |
| Unsupported `mode` | Validation error |
| Invalid email | Validation error |
| Extra payload keys | Ignored by allowlist |
| Credit limit or payment terms in payload | Ignored by allowlist |
| Missing required new-customer fields | Validation error |
| Duplicate customer candidate | Duplicate warning, not automatic creation |

Decision:

`Accept for Sales Manager/Sales User role gate; actual customer save persistence remains a manual freeze check if required`

## 10. Restricted-State Behavior

Expected restricted states:

1. no Customer read permission: Customer page shows restricted state
2. no Item read permission: Item page shows restricted state
3. no Quotation read permission: Quotation directory shows restricted state
4. no Sales Order read permission: Sales Order directory shows restricted state
5. no Payment Entry read permission: Sales Invoice page hides payment-entry detail
6. customer outside Sales Console scope: Customer detail/edit refuses access
7. bare worklist route: guarded unavailable state, not raw ERP fallback

Decision:

`Accept pending browser verification`

## 11. Browser And Role Verification Script

Before promoting Sales Console as a final golden reference, run this manual verification.

### 11.1 Sales User

1. Open Sales Console.
2. Confirm Customers page is readable only for visible accounts.
3. Confirm Create Customer is not available.
4. Confirm Edit Customer is not available.
5. Attempt direct customer-editor route and confirm restricted state.
6. Attempt direct save API if possible and confirm server rejects it.

### 11.2 Sales Manager

1. Open Customers page.
2. Confirm Create Customer is available.
3. Create a test customer with name, group, territory, phone, and email.
4. Confirm save stays in Sales Console and returns saved truth.
5. Reopen the customer detail page after browser refresh.
6. Edit only allowed fields and confirm they persist.
7. Confirm credit limit, payment terms, tax settings, account controls, and delete are not exposed.

### 11.3 Payment Visibility

1. Use a role with Sales Invoice read but without Payment Entry read.
2. Open a Sales Invoice page with linked payment records.
3. Confirm payment-entry detail and count do not leak.
4. Use a role with Payment Entry read and confirm payment context appears only then.

### 11.4 Direct Inquiry

1. Search a visible customer/document and confirm inquiry resolves.
2. Try a known invisible document ID if available.
3. Confirm the response is unavailable/restricted and does not expose customer, amount, date, or chain details.

### 11.5 Restricted Worklists

1. Remove or simulate missing read permission for Customer, Item, Quotation, and Sales Order separately.
2. Confirm each page shows a controlled restricted state.
3. Confirm no raw native list route is opened automatically.

## 12. SERA-2 Exit Criteria

| Exit criterion | Status |
| --- | --- |
| Whitelisted methods inventoried | Pass |
| Guest rejection checked in code | Pass |
| Customer mutation gate checked | Pass |
| Allowed-field contract checked | Pass |
| Customer save returns saved truth | Pass |
| Direct inquiry record read hardened | Pass |
| Customer parent reads permission-aware | Pass |
| Item parent reads permission-aware | Pass |
| Payment Entry detail guarded | Pass |
| Unsafe backend delete/submit/cancel bypass absent | Pass |
| Contact permission elevation documented | Conditional Pass |
| Live role/browser verification complete | Pass for Sales Manager/Sales User core gate |

## 13. Remaining Risks

### 13.1 Contact Permission Elevation

Risk:

Contact phone/email synchronization uses controlled permission elevation.

Recommendation:

Keep it for V1 because it supports the intended Sales Manager workflow. The live role gate was verified with real Sales Manager and Sales User accounts on 2026-05-01; an actual contact-save mutation was intentionally not performed during the smoke pass.

If future policy says Contact permission must be strict, replace the elevation with a native Contact permission requirement and show a business-friendly restricted message.

### 13.2 Report Builder Depth

Risk:

SERA-2 reviewed report access at the surface level. Some report builders call native reports and assemble business metrics.

Recommendation:

Review each report family in SERA-4 page archetype audit.

### 13.3 AI Assist Exists Before Final AI Design

Risk:

Customer inquiry AI assist already exists as a read-only helper, while the program direction says major AI features are deferred until workspace foundations are complete.

Recommendation:

Do not expand AI features during SERA. Keep this helper read-only, fallback-safe, and non-authoritative until the future AI feature design phase.

### 13.4 Remaining Role Evidence Boundary

Risk:

The 2026-05-01 live role smoke proves the Sales Manager and Sales User gate, but it does not prove every future role family or an actual customer save mutation.

Recommendation:

Repeat the role smoke before future freeze decisions and run a controlled customer save only if the freeze decision requires persistence proof with a disposable or approved customer record.

## 14. Go/No-Go For SERA-3

Decision:

`Go for manual freeze review with Sales Manager/Sales User role gate verified`

Reason:

The code-level blockers found in SERA-2 have been hardened, and the Sales Manager/Sales User live role/browser proof passed on 2026-05-01.

Condition:

Sales Console must not be promoted as the final reusable golden reference until the user accepts the manual visual freeze review and any deliberately chosen save-persistence proof.
