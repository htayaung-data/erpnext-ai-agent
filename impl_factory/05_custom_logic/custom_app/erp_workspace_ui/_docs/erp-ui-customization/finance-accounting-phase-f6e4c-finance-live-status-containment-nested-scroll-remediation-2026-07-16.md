# F6E4C Finance Live-Status Containment and Nested-Scroll Remediation

Date: 2026-07-16
Status: Source remediation pending independent counterpart review

## Confirmed defect

Authenticated live geometry established two independent vertical scroll owners on Finance Control Desk: the Desk `.main-section` and `document.scrollingElement`. The persistent polite Finance status element was `position: absolute` under a static Frappe Page body, had no `offsetParent`, and used its static position at the end of Finance content in the initial containing block. That escaped 1px element extended the document by the same 235px as the legitimate Desk content range.

Finance mount ownership was already correct and remains unchanged: supplied route wrapper to `wrapper.page.body` to the Finance presentation content. No duplicate Page, excess shell minimum height, or shared Desk overflow rule caused the defect.

## Minimal source correction

- The Finance Page body now contains exactly one Finance-owned presentation shell.
- The shell contains both the persistent render host and persistent polite live-status region.
- The shell uses `position: relative`; the live status uses local `top: 0` and `left: 0` coordinates with no negative margin.
- The live status remains clipped visually, exposed as an atomic polite status, and persistent across state rendering.
- Existing repeated-announcement, Refresh focus-intent, timeout, supersession, route-departure, return, payload, role, and accounting behavior is unchanged.
- No fixed height, global overflow rule, document mount, outer-wrapper mount, or scroll suppression was introduced.

## Evidence contract

The actual registered Finance renderer and Frappe-style Page fixture cover manager-ready, Accounts User manager-only unavailable, restricted, controlled-unavailable, and transport-error states at 1366px, 390px, and 320px. The renderer evidence now requires:

- one wrapper-owned Frappe Page body and one owned Finance presentation shell;
- a non-null live-status `offsetParent` equal to that presentation shell;
- a live-status rectangle contained by the presentation shell;
- no independent `document.scrollingElement` vertical range;
- `.main-section` as the natural content scroll owner;
- no horizontal overflow, clipping, overlap, or artificial trailing extent;
- long Finance content remains fully reachable through the Desk scroller;
- repeated identical authoritative outcomes still repopulate the persistent live region.

This is source-renderer evidence. It is not authenticated post-alignment browser acceptance.

## Source and live truth

The Finance page JavaScript is the only runtime candidate for a later controlled F6E4C alignment:

- Source: `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`
  - SHA-256: `d05b6bce8ca5f755e871e1814435580d55cbd2c8fe691de7e8f98fac96c4b72c`
- Live remains at SHA-256: `8f1d1839a95f23839305d8efd7a7d2f04e774b60d1f5ddcfa576528041a14fd9`

The Finance service, shared sidebar, registry, governance, routing, Page metadata, roles, permissions, company scope, AR/AP semantics, payload contract, and execution boundaries are unchanged. Tests, smokes, README, and this document are source evidence and are not runtime alignment files.

## Exact source package manifest

The F6E4C source package is exactly these six paths:

1. `_docs/erp-ui-customization/README.md`
   - SHA-256: `66979a35f3cc824fd60bb2ce40dbd5b871c003ce4314677de8e77022638b6ba9`
2. `_docs/erp-ui-customization/finance-accounting-phase-f6e4c-finance-live-status-containment-nested-scroll-remediation-2026-07-16.md`
   - Its final SHA-256 is recorded by the validation report because a document cannot embed its own final content hash.
3. `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`
   - SHA-256: `d05b6bce8ca5f755e871e1814435580d55cbd2c8fe691de7e8f98fac96c4b72c`
4. `erp_workspace_ui/tests/test_finance_accounting_shell.py`
   - SHA-256: `685fd27d4f490dcdc5c69777ec1bfd6adba20598bb048896a95577c1599857e1`
5. `ui_smoke/finance_cycle1_source_smoke.js`
   - SHA-256: `fafaa7cdd8622b34f6b924ff9aed5d6717cb15314ebd01f8e1dd5ae9782c1eb2`
6. `ui_smoke/finance_cycle1_responsive_smoke.js`
   - SHA-256: `b8388d47bbd21d63c99692b3c5f23b05cbaec6e62cc1e3de38014cb596778f86`

Only item 3 is a future runtime-alignment candidate. The other five paths are documentation or source-validation evidence.

## Gates

No live alignment, restart, cache clear, metadata reload, migration, staging, commit, push, permission change, protected gate, or accounting action occurred. Independent counterpart review must report no Blocker or High finding before the one-file runtime alignment can be considered. F6F remains blocked until later authenticated Finance Manager and Accounts User browser acceptance passes.
