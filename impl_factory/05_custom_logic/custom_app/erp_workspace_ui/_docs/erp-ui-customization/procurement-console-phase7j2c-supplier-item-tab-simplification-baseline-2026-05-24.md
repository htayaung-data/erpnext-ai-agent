# Procurement Console Phase 7J2C Supplier / Item Tab Simplification Baseline

Date: 2026-05-24
Branch: `feature/erpnext-ui-design`
Accepted commit: `268e443451742fd10cf6ea705e17880101685005`
Baseline type: protected docs-only closure after accepted runtime implementation

## 1. Status

Phase 7J2C is closed as a protected baseline for the simplified Supplier Detail and Buying Item Detail object-page tabs.

Owner and Main Agent manual/visual review accepted the implementation at commit `268e443451742fd10cf6ea705e17880101685005`. This document records the accepted evidence and operating contract. It does not introduce runtime, smoke, test, data, or live changes.

## 2. Closure Summary

Phase 7J2C simplified the Phase 7J2A tabbed object pages after Phase 7J2B review found the first tab set still too busy.

Accepted Supplier Detail behavior:

- Default tab is `Profile`.
- Visible tabs are only `Profile`, `Orders`, `RFQs`, and `Quotations`.
- Removed `Activity`, standalone `Readiness Guidance`, and standalone `References` tabs.
- `Profile` contains Supplier Buying Profile, readiness/status guidance, buying contact/reference context, and the controlled Purchase Manager edit affordance already approved by earlier phases.
- Duplicate below-header badge clutter was removed.
- Purchase User remains read-only and productized.

Accepted Buying Item Detail behavior:

- Default tab is `Profile`.
- Visible tabs are only `Profile`, `Suppliers & Prices`, `Orders`, and `Quotation History`.
- Removed standalone `Readiness Guidance`, standalone `References`, and `Demand & Orders` tab clutter.
- The visible profile label is `Item Buying Context`.
- `Profile` contains Item Buying Context, readiness/status guidance, relevant reference context, and the controlled Purchase Manager edit affordance already approved by earlier phases.
- Duplicate below-header badge clutter was removed.
- Purchase User remains read-only and productized.

The phase did not add Quick Find, new backend pagination, full-history endpoints, master-data mutation, lifecycle actions, send/email behavior, or native ERP form escape.

## 3. Protected Tab Contract

Future changes must preserve this baseline unless owner approval explicitly opens a new implementation phase.

| Page | Default tab | Protected tab set |
| --- | --- | --- |
| Supplier Detail | `Profile` | `Profile`, `Orders`, `RFQs`, `Quotations` |
| Buying Item Detail | `Profile` | `Profile`, `Suppliers & Prices`, `Orders`, `Quotation History` |

Removed labels must not return as visible tabs in the protected baseline:

- `Activity`
- `Readiness Guidance`
- `References`
- `Demand & Orders`, unless a later approved phase adds real demand rows and owner accepts the label

Duplicate below-header object badge rows must not return. Healthy/read-only states should remain low-noise and should not add extra badge clutter.

## 4. Role Contract

Purchase Manager:

- May see controlled edit affordances already approved for Supplier Buying Profile and Item Buying Context.
- Must remain inside productized Procurement routes.
- Must not receive native ERP form escape controls.

Purchase User:

- Uses the same default `Profile` landing tab on both detail pages.
- Remains read-only/productized.
- Must not see hidden admin/native actions.
- Must not receive master-data mutation controls.

## 5. Validation Evidence

Accepted implementation and validation evidence:

- Focused source Phase 7J2C smoke: `/tmp/procurement-phase7j2c-source-smoke-20260524T014253Z`
- Source Sales freeze: `/tmp/procurement-phase7j2c-sales-freeze-source-20260524T015630Z`
- Source protected gate: `/tmp/procurement-phase7j2c-protected-source-20260524T034538Z`
- Focused live Phase 7J2C smoke: `/tmp/procurement-phase7j2c-live-smoke-20260524T040946Z`
- Final post-live protected gate: `/tmp/procurement-phase7j2c-protected-live-rerun-20260524T045633Z`
- Sales freeze inside final gate: `/tmp/procurement-phase7j2c-protected-live-rerun-20260524T045633Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Post-live protected gate status:

- Overall status: pass.
- Head commit: `268e443451742fd10cf6ea705e17880101685005`.
- Sales freeze inside protected gate: pass.
- Procurement protected stages: pass.
- Artifact stale/failure check: pass.

One earlier post-live protected gate attempt failed in `sales-directory-performance`; a focused rerun passed at `/tmp/procurement-phase7j2c-sales-directory-focused-live-20260524T045530Z`, and the full protected gate rerun passed. That incident was classified as transient Sales route-load timing, not a Phase 7J2C Procurement runtime defect.

Source validation during implementation closure:

- `python3 -m compileall erp_workspace_ui` passed.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'` passed with 221 tests.
- Node syntax checks passed for touched runtime and smoke files.
- `git diff --check HEAD` passed.
- Static native escape, send-removal, and lifecycle/conversion forbidden scans passed.

## 6. Source / Live Hashes

The accepted runtime source/live hashes after live alignment were:

| File | SHA-256 |
| --- | --- |
| `erp_workspace_ui/public/js/procurement_console/procurement_console_supplier_page.js` | `92e5925b71b0973a031b9a80acfa1fdc4a602b5fcbebe2a3b3d5771feeb5a3d0` |
| `erp_workspace_ui/public/js/procurement_console/procurement_console_item_page.js` | `8790e999b5a959d1fd152c14d1cc05db421ac3502833c1333fc9b93dd0f4f8f5` |

## 7. Protected Behavior Contract

Future changes must preserve:

- Supplier Detail lands on `Profile`.
- Buying Item Detail lands on `Profile`.
- Supplier Detail tab set remains exactly `Profile`, `Orders`, `RFQs`, `Quotations`.
- Buying Item Detail tab set remains exactly `Profile`, `Suppliers & Prices`, `Orders`, `Quotation History`.
- `Item Buying Context` remains the visible buying context label.
- Purchase User remains read-only/productized.
- Productized Procurement routes remain the only normal-role navigation path.
- Long object-specific lists stay inside their object tabs and do not flood the first viewport.
- No duplicate shell/header/sidebar appears at 1136, 1240, or 1440 widths.
- No horizontal overflow or clipped action controls are introduced.

## 8. Forbidden / Deferred Scope

Phase 7J2C did not introduce or start:

- Sales runtime changes.
- Native ERP form escape.
- RFQ or PO send.
- Email/SMTP runtime.
- Communication or Email Queue creation.
- Contact, User, or portal creation.
- Submit, approval, rejection, cancel, amend, or conversion lifecycle actions.
- Receiving, billing, or payment mutation.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- AI intake.
- Quick Find.

## 9. Manual Check Instructions

As Purchase Manager:

1. Open Supplier Detail at 1136px.
2. Confirm `Profile` is active by default and the only tabs are `Profile`, `Orders`, `RFQs`, and `Quotations`.
3. Confirm `Activity`, `Readiness Guidance`, and `References` are absent as tabs.
4. Open Buying Item Detail at 1136px.
5. Confirm `Profile` is active by default and the only tabs are `Profile`, `Suppliers & Prices`, `Orders`, and `Quotation History`.
6. Confirm the visible profile label is `Item Buying Context`.
7. Confirm duplicate below-header badge clutter is absent.

As Purchase User:

1. Open Supplier Detail and Buying Item Detail.
2. Confirm both pages land on `Profile`.
3. Confirm the pages remain read-only/productized.
4. Confirm no native ERP form escape, hidden admin action, or mutation action is visible.

## 10. Recommended Next Task

Recommended next implementation task:

`Phase 7K Overview Quick Find implementation`

Phase 7K must remain separate from this baseline and must preserve all protected Phase 7J2C behavior.
