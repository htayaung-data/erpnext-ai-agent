# Warehouse Console Phase W15I2 Implementation Gap Audit Matrix

Decision: `audit_ready_for_patch_planning`

Date: 2026-06-27

Scope: documentation and audit only. W15I2 audits W15E/F/G/H implementation against the W15I1 Hardening, Security/Stability, and Operations contracts. W15I2 does not implement source hardening patches, runtime UI, backend methods, DocTypes, tests, smokes, live files, route behavior, native ERPNext links, stock documents, stock mutation, Sales runtime, Procurement runtime, notification behavior, commits, pushes, live alignment, restarts, or protected gates.

## 1. Purpose

W15I2 is the first contract-driven implementation audit after the W15I1 review contracts were written.

The goal is to identify actual implementation gaps before activating any planned Warehouse workflow UI or opening any ERPNext document runtime.

This audit uses the Hybrid Review Ladder:

- Main Control performed source verification and matrix integration.
- Internal subagent preflight reviewed W15E/F customer/supplier return backend methods.
- Internal subagent preflight reviewed W15G/H internal transfer and cycle count backend methods.
- Internal subagent preflight reviewed W15E/F/G/H DocType metadata, Overview shells, and W9A smoke coverage.
- Separate Hardening, Security/Stability, and Operations agents remain required before any phase-ending acceptance or source patch batch.

## 2. Audited Implementation Surfaces

Service methods:

- `save_warehouse_customer_return_intake_draft`
- `save_warehouse_customer_return_manager_decision`
- `request_warehouse_customer_return_handoff`
- `save_warehouse_supplier_return_candidate_draft`
- `save_warehouse_supplier_return_manager_decision`
- `request_warehouse_supplier_return_handoff`
- `save_warehouse_internal_transfer_candidate_draft`
- `save_warehouse_internal_transfer_manager_decision`
- `request_warehouse_internal_transfer_handoff`
- `save_warehouse_cycle_count_task_draft`
- `save_warehouse_cycle_count_manager_decision`
- `request_warehouse_inventory_variance_handoff`

Custom DocType groups:

- `Warehouse Customer Return Intake`
- `Warehouse Customer Return Handoff Request`
- `Warehouse Supplier Return Candidate`
- `Warehouse Supplier Return Handoff Request`
- `Warehouse Internal Transfer Candidate`
- `Warehouse Internal Transfer Handoff Request`
- `Warehouse Cycle Count Task`
- `Warehouse Inventory Variance Handoff Request`

UI and smoke surfaces:

- Warehouse Overview planned workflow shells for Customer Return, Supplier Return, Internal Transfer, and Cycle Count / Inventory Variance.
- W9A cockpit smoke assertions for shell count, planned controls, active-control absence, guardrail copy, and native-route absence.

## 3. Executive Summary

W15I2 found no evidence of ERPNext stock/accounting/customer/supplier document mutation, native route exposure, valuation/accounting/commercial exposure, notification/email/portal behavior, Sales runtime changes, or Procurement runtime changes in the audited W15E/F/G/H implementation.

The major gaps are contract-hardening gaps:

- Manager-decision idempotency compares only event type in several tracks, so the same `request_id` and same decision can return idempotently even if note/reference details changed.
- Handoff `request_id` ownership is too narrow in several tracks and does not consistently reject reuse of source draft or manager-event request ids.
- Supplier return manager decision request-id ownership misses draft request ids.
- Some draft line payloads silently ignore unknown or forbidden line fields instead of explicitly rejecting them.
- Some draft line payloads truncate over-limit input instead of rejecting.
- Event records are custom-only, but current event schemas are minimal and do not yet expose W15I minimum audit fields as first-class fields.

Recommended next step: W15I3 should patch High gaps first in a small source batch, then rerun unit tests and send the batch through separate Hardening, Security/Stability, and Operations agents.

## 4. Gap Matrix

| ID | Track | Artifact Type | Current Implementation | Required Contract | Gap | Severity | Patch Recommendation | Reviewer Required | Owner Manual Check Required | Boundary Risk |
|---|---|---|---|---|---|---|---|---|---|---|
| W15I2-H01 | W15E/W15F/W15G/W15H manager decisions | Service method + unit tests | Existing idempotent manager retry checks compare request event type only. Same request id plus same decision can return idempotently even if note, escalation reference, Inventory/Admin reference, quarantine reference, or manager detail changed. | Same request id with changed payload must reject. Manager decision idempotency must compare canonical decision payload, not only event type. | Changed same-decision manager payload can be accepted as idempotent. | High | Add canonical manager decision payload hash or compare normalized event details for each manager decision path. Add same-decision changed-note/reference tests for customer return, supplier return, internal transfer, and cycle count. | Hardening, Security/Stability, Operations | No | Idempotency and audit integrity |
| W15I2-H02 | W15E/W15F/W15G/W15H handoff requests | Service method + unit tests | Handoff request-id owner helpers primarily check existing handoff request rows. They do not consistently check source draft request ids or source manager-event request ids before creating a new handoff request. | Original draft request id and manager-event request id must not be reused for handoff actions unless explicitly allowed. Cross-action request-id reuse must reject. | Handoff request ids can collide with source action request ids, weakening audit/idempotency separation. | High | Extend handoff request-id ownership checks to source parent DocTypes and source event DocTypes, or add a shared per-track request-id registry helper. Add tests reusing draft and manager request ids for each handoff path. | Hardening, Security/Stability | No | Cross-action request-id and audit integrity |
| W15I2-H03 | W15F supplier return manager decision | Service method + unit tests | Supplier manager request-id owner lookup checks supplier return event rows only. It does not check `Warehouse Supplier Return Candidate.request_id` before resolving event owner. | Manager request id cannot reuse the original draft request id across candidates. | Cross-source reuse of a supplier candidate draft request id can pass owner lookup until later same-source check, leaving a cross-candidate gap. | High | Make supplier manager owner lookup check supplier candidate parent `request_id` first, matching the safer customer-return pattern. Add cross-draft reuse tests. | Hardening, Security/Stability | No | Cross-source request-id integrity |
| W15I2-H04 | W15E/W15F draft line inputs | Service method + unit tests | Customer return and supplier return line normalizers read known keys and can ignore unknown non-empty line keys. | Unknown non-empty line fields and forbidden line fields must reject. | Client-supplied forbidden line fields may be silently ignored rather than explicitly rejected. | High | Add allowed-line-field sets and non-empty unknown line rejection for customer return intake and supplier return candidate lines. Add line-level forbidden field tests. | Hardening, Security/Stability | No | Payload boundary integrity |
| W15I2-M01 | W15E/W15F manager and handoff methods | Service method + tests | Some customer/supplier manager and handoff method signatures do not accept `**extra_fields`; unknown fields are rejected by Python signature behavior rather than explicit forbidden-field policy. | Forbidden stock, native route, valuation, notification, Sales, and Procurement fields should be explicitly rejected by service validation. | Contract behavior is implicit and less testable. | Medium | Add `**extra_fields` plus shared forbidden-field validation to customer/supplier manager and handoff methods. Add forbidden field tests. | Hardening, Security/Stability | No | Explicit rejection and testability |
| W15I2-M02 | W15E customer return intake draft | Service method + unit tests | Customer return lines are processed with `raw_lines[:CUSTOMER_RETURN_INTAKE_MAX_LINES]`, truncating over-limit payloads. Supplier return correctly rejects over max. | Excessive line count must reject, not silently truncate. | Over-limit customer return payload can lose client-supplied lines silently. | Medium | Add explicit `len(raw_lines) > CUSTOMER_RETURN_INTAKE_MAX_LINES` rejection and a test mirroring supplier return. | Hardening, Operations | No | Payload completeness |
| W15I2-M03 | W15F supplier return handoff | Service method + DocType metadata | Supplier candidate accepts `overage_qty` and `quality_hold_qty`, but supplier handoff derived lines do not carry those quantities forward. | Handoff rows should preserve or explicitly summarize source evidence that drives downstream review. | Procurement/Admin handoff can drop supplier-return evidence dimensions. | Medium | Either add fields to supplier handoff line metadata/payload/hash, or map them into reason/evidence summary with explicit tests. | Operations, Hardening | Yes | Business evidence continuity |
| W15I2-M04 | W15H inventory variance handoff | Service method + unit tests | Handoff line derivation validates item identity and warehouse, but does not revalidate non-negative quantities, allowed variance direction/status, or evidence requirements from the source task line. | Derived lines should still fail closed if persisted source data is malformed or tampered. | Malformed source line data could be carried into a custom handoff request. | Medium | Reuse/factor cycle-count line validators for handoff derivation. Add tampered-source tests for negative quantity, invalid direction/status, and missing evidence. | Hardening, Security/Stability | No | Source-derived line integrity |
| W15I2-M05 | W15E/F/G/H event records | DocType metadata + service audit | Event child DocTypes are custom-only and include `event_type`, `event_label`, `event_by`, `event_at`, `request_id`, and `details_json`; they do not expose W15I minimum audit fields as first-class fields. | W15I audit contract calls for source doctype/name/line, target workflow, old/new state, actor role family, payload hash, validation result, and note/evidence summary. | Audit trail exists but is less structured than the W15I standard. | Medium | Add a later audit-event normalization phase or document an accepted `details_json` schema and tests. Prefer first-class fields for source/state/hash/role family where feasible. | Hardening, Security/Stability | No | Audit completeness |
| W15I2-M06 | W15E/F/G/H event fields | DocType metadata + tests | Event core fields are not consistently marked required across event child DocTypes. | Core audit fields should be required where event rows exist. | Event rows could be malformed through direct metadata/native form paths if ever exposed. | Medium | Mark at least `event_type`, `event_by`, `event_at`, and `request_id` required consistently, or document why service-only child rows make metadata requiredness unnecessary. | Security/Stability, Hardening | No | Audit metadata integrity |
| W15I2-M07 | W15H cycle count task | DocType metadata | `Warehouse Cycle Count Task.request_id` is present but not marked required in metadata. Service requires request id. | Request-tracked parent metadata should align with service contract where feasible. | Metadata and service contract are inconsistent. | Medium | Set `request_id` required in `Warehouse Cycle Count Task`, or document why service-only creation makes metadata requiredness unnecessary. | Hardening, Security/Stability | No | Audit correlation |
| W15I2-M08 | W15E/F/G/H request-id owner helpers | Service helpers + tests | Several owner helpers request up to two rows but return the first row without throwing if duplicates exist. | Ambiguous duplicate request-id state should fail closed. | Duplicate request id rows from race/manual corruption could make idempotency ambiguous. | Medium | If feasible, add unique constraints or throw when lookup returns more than one row. Add helper tests or service tests for duplicate-row behavior in the mock layer. | Security/Stability, Hardening | No | Duplicate request-id integrity |
| W15I2-L01 | W15H cycle count tests | Unit tests | W15H4/W15H5 safe-payload tests check `GET_DOC_CALLS` but do not consistently assert `GET_ALL_CALLS` forbidden-doctype absence like nearby handoff tests. | Safe-payload tests should include parent document fetch and list fetch negatives where applicable. | Minor negative-test coverage gap. | Low | Add `GET_ALL_CALLS` forbidden-doctype assertions to W15H4/W15H5 safe-payload tests. | Hardening | No | Negative-test explicitness |
| W15I2-L02 | W15E/F/G/H metadata | DocType metadata | `index_web_pages_for_search` is `0`, but `allow_web_indexing` is absent in the inspected DocTypes. | Web indexing should be explicitly disabled where the framework supports both flags. | Likely default-safe, but less explicit than W15I1 wording. | Low | Add `"allow_web_indexing": 0` to W15E/F/G/H custom DocTypes if compatible with the current ERPNext/Frappe version. | Security/Stability | No | Web indexing explicitness |
| W15I2-L03 | W15H Overview planned shell | UI copy + smoke | One planned policy card uses technical wording such as `Native routes`, which is less owner-facing than the rest of the premium UI. | Owner-facing UI should avoid raw technical/security terms where business wording is clearer. | Minor Operations wording issue. | Low | Replace with `Direct ERP document pages` or `System document access`, and optionally add smoke coverage for `native route` wording absence. | Operations | Yes | Owner-facing clarity |
| W15I2-L04 | W15E customer return line wording | DocType metadata + future UI | Customer intake line field remains `accepted_qty`; handoff uses safer `accepted_for_intake_qty`. | Future UI should avoid wording that implies stock acceptance. | Backend field name is read-only but could influence future UI labels. | Low | Keep UI label as `accepted for intake` / `accepted return count`; do not expose `accepted_qty` raw. Consider alias/mapping in future UI. | Operations | Yes | Stock-action implication |

## 5. Confirmed Clean Or Acceptable Areas

No material gap found in these areas during W15I2:

- Parent custom DocTypes are non-submittable.
- Parent custom DocTypes are not web-indexed through `index_web_pages_for_search`.
- Parent custom DocType actions and links are empty.
- Child DocTypes are child tables with no direct permissions.
- Parent permission families broadly match policy: evidence parents allow Warehouse/Stock users create-write; handoff parents keep Warehouse/Stock users read-only; manager roles can create-write where approved.
- Forbidden field types were not found in inspected DocTypes: `Link`, `Dynamic Link`, `Attach`, `Attach Image`, `HTML`, `Button`, `Currency`.
- Planned Overview shell controls remain inert.
- W9A smoke covers shell count, planned-control count, zero active controls, guardrail copy, and no native route exposure for planned shells.
- No source evidence was found for Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, Purchase Invoice return/debit note, stock movement/posting, native route exposure, valuation/accounting/commercial exposure, customer/supplier notification, Sales runtime change, or Procurement runtime change.

## 6. Subagent Finding Not Accepted As A Current Gap

One metadata/UI subagent flagged stub or missing DocType controllers as a possible event persistence issue. Main Control does not treat this as a standalone W15I2 gap because these custom records are service-owned and service methods append child event rows directly before `insert()` or `save()`.

The accepted gap is narrower: event rows exist but are not yet normalized to the W15I minimum first-class audit field standard.

## 7. Recommended Patch Sequence

W15I3 should patch High gaps first:

1. Add canonical manager-decision idempotency payload comparison for W15E/F/G/H.
2. Add same-decision changed-note/reference tests for W15E/F/G/H.
3. Extend handoff request-id ownership checks to source draft and source event rows for W15E/F/G/H.
4. Fix W15F supplier manager request-id owner lookup to include source draft rows.
5. Add unknown/forbidden line-field rejection for W15E/F draft line inputs.

W15I4 should patch Medium validation gaps:

1. Explicit forbidden `**extra_fields` handling for W15E/F manager/handoff methods.
2. Unknown/forbidden line-field rejection for W15E/F draft line inputs.
3. Customer return max-line rejection instead of truncation.
4. Supplier handoff evidence preservation for overage and quality-hold quantities.
5. Inventory variance handoff source-line semantic revalidation.

W15I5 should patch audit/metadata/UI polish:

1. Event field requiredness and audit-field normalization decision.
2. Cycle count task `request_id` metadata requiredness.
3. Optional explicit `allow_web_indexing: 0`.
4. W15H UI technical wording cleanup.
5. W15H4/W15H5 `GET_ALL_CALLS` negative assertions.

No planned workflow activation should start until W15I3 and W15I4 are accepted.

## 8. Validation Performed

Read-only validation and inspection performed:

- `git status --short --branch`.
- Service method mapping for W15E/F/G/H.
- Custom DocType folder inventory for W15E/F/G/H.
- Unit test method inventory for W15E/F/G/H.
- Warehouse Overview planned shell and W9A smoke selector inventory.
- Event child DocType field summary.
- Focused source inspection for manager idempotency, request-id owner helpers, customer max-line handling, supplier max-line handling, and inventory variance handoff derivation.
- Hybrid Review Ladder subagent preflight for W15E/F backend, W15G/H backend, and metadata/UI/smoke.

No unit tests, compileall, node checks, live smokes, commits, pushes, live alignment, restarts, or protected gates were run for W15I2 because this phase is audit-only.

## 9. Boundary Confirmation

W15I2 is documentation and audit only. It introduces no runtime/backend method, DocType metadata, test, smoke, live file, commit, push, live alignment, restart, protected gate, ERPNext stock document behavior, stock mutation, native route exposure, valuation/accounting/commercial exposure, Sales runtime, Procurement runtime, notification/email/portal behavior, or external action.
