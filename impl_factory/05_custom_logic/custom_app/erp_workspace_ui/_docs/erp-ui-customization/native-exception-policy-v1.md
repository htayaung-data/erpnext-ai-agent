# Native Exception Policy v1

Date: 2026-05-06
Status: Mandatory shared-core governance policy
Applies to: Sales Console, Procurement Console, and future ERP workspaces
Related docs: `shared-core-workspace-adapter-contract-v2.md`, `shared-core-route-action-inventory-2026-05-06.md`

## 1. Purpose

ERPNext native pages are sometimes required because ERPNext owns document lifecycle, workflow, validation, permissions, grid behavior, and conversion tools. Those legitimate native surfaces must be governed. Accidental native leakage from productized workspace pages is not acceptable.

This policy defines which native surfaces are currently allowed, where they may appear, and how future work must declare them.

## 2. Definitions

A governed native exception is an approved route or action where the workspace intentionally opens an ERPNext native form or native lifecycle surface while keeping workspace context and permission boundaries intact.

Bad leakage is an unapproved route or action where a productized workspace page sends users to raw ERPNext pages as the default experience, bypasses the productized route family, or exposes mutation controls that the workspace has not been approved to own.

The key difference is intent, declaration, permission gating, chrome control, and browser evidence.

## 3. Allowed Governed Native Exceptions

Current allowed exception families:

| Exception id | Workspace | Native surface | Status | Boundary |
| --- | --- | --- | --- | --- |
| `sales-managed-document-forms-v1` | Sales | Quotation, Sales Order, Delivery Note, Sales Invoice forms wired through `doctype_js` | Approved for Sales freeze | ERPNext owns save, submit, print, email, assignment, sharing, and workflow truth. |
| `procurement-native-create-forms-phase3-v1` | Procurement | New Purchase Material Request, New RFQ, New Supplier Quotation, New Purchase Order | Approved Phase 3 exception | ERPNext owns create workflow and form tools. Procurement supplies workspace chrome/context. |
| `procurement-secondary-native-open-v1` | Procurement | Secondary open/edit actions for Purchase Request, RFQ, Supplier Quotation, Supplier, and Item where current code permission-gates them | Allowed as secondary governed actions only | Productized review/detail remains primary. Native form access must not be the primary row action. |

The Procurement native create-form exception is temporary governance, not the final premium form direction. If the owner approves replacing these native forms later, the future phase name is `Managed Procurement Forms`.

## 4. Allowed Native Controls Inside Governed Exceptions

The following ERPNext controls are allowed inside an approved native exception when ERPNext permissions and workflow expose them:

1. `Get Items From`
2. `Tools`
3. `Save`
4. `Add row`
5. `Add multiple`
6. grid row controls
7. grid download/upload controls
8. document conversion helpers
9. print, email, assignment, sharing, comments, attachments, tags, and timeline controls where ERPNext owns them
10. workflow buttons that ERPNext shows according to native workflow and role permissions

These controls are not bad leakage when they appear inside an approved native form body. They become leakage if copied into productized read-only pages or exposed as unapproved workspace mutations.

## 5. Not Allowed On Productized Pages

Productized overview, worklist, report, detail, and read-only review pages must not expose:

1. generic `Open ERP Form` as a primary row action
2. direct native form route as the default row action when a productized route exists
3. native `Submit`, `Cancel`, `Amend`, `Close`, `Unclose`, `Approve`, or `Reject` actions unless a managed mutation page has been explicitly approved
4. native `Receive`, `Bill`, or `Pay` actions from Procurement pages
5. `Set Default Supplier` or `Update Item Price` mutations from Procurement Phase 3 pages
6. `Delete` by default
7. raw ERPNext module menus mixed into normal workspace navigation
8. native report or list fallbacks that bypass an available productized report/worklist route

Native fallback links may exist only when classified as governed secondary actions or fallback actions in the route/action manifest.

## 6. Native Exception Requirements

Every governed native exception must be declared in the manifest with:

1. exception id
2. workspace id
3. route or action key
4. route/action classification
5. native DocType or report target
6. owning adapter
7. expected shell/chrome
8. role and permission boundary
9. primary versus secondary action posture
10. required smoke category
11. notes for temporary or future replacement status

Any exception missing a manifest entry is ungoverned and must be treated as leakage until classified.

## 7. Chrome And Breadcrumb Requirements

Governed native exceptions must keep workspace context:

1. correct workspace sidebar where the workspace launched the native form
2. clean workspace breadcrumb/header
3. no duplicate native/productized headers
4. no stale previous productized content
5. no page stacking after repeated navigation
6. direct refresh should reconstruct a safe workspace context where possible
7. native ERP form body remains visibly and behaviorally owned by ERPNext

A native form with correct ERPNext behavior but stale workspace chrome still fails this policy.

## 8. Productized Page Requirements

Productized pages must use productized route targets as their primary path:

1. Procurement Purchase Request rows route to Purchase Request Review
2. Procurement RFQ rows route to RFQ Review
3. Procurement Supplier Quotation rows route to Supplier Quotation Review
4. Procurement Supplier and Buying Item detail PO rows route to Procurement PO Follow-up Detail
5. Sales Customer and Item rows route to productized Sales detail pages
6. Sales managed document rows may route to approved managed Sales forms where ERPNext remains transaction truth

A secondary governed native action can exist only when declared and permission-gated.

## 9. Browser Smoke Coverage

Governed native exceptions need browser evidence when they are introduced or changed:

1. route opens with expected workspace chrome
2. native form tools render normally inside the form body
3. no duplicate headers appear
4. no native parent module route is exposed as the workspace parent
5. back/refresh/re-entry do not stack stale content
6. role permissions control the action or route
7. productized worklists still use productized primary row actions

Existing smoke suites may be used. Do not install new Node, Playwright, system packages, Docker images, Caddy rules, bench config, or app config just for this policy.

## 10. Forbidden Mutation Guard

The route/action manifest must keep a forbidden mutation guard list. These labels are forbidden on productized read-only/worklist/report/detail pages unless a future managed mutation page explicitly approves them:

`Submit`, `Cancel`, `Amend`, `Close`, `Unclose`, `Approve`, `Reject`, `Receive`, `Bill`, `Pay`, `Set Default Supplier`, `Update Item Price`, `Delete`.

The guard does not forbid ERPNext from showing legitimate lifecycle buttons inside approved native exceptions.

## 11. Repair Classification

If a current or future route/action is found to be leakage, classify it as `not_allowed_leakage` in the manifest with:

1. repair owner or phase
2. status
3. reason it is unsafe
4. safe target or intended replacement
5. test or smoke that should fail until it is repaired

A `not_allowed_leakage` entry without owner/status is not allowed to pass contract tests.
