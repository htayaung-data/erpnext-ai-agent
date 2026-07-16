# F6E4A Finance Page Host Geometry and Trailing Scroll Remediation

Date: 2026-07-15
Status: Strict-ownership remediation ready for repeat independent counterpart review

## Finding

Finance rendered directly into the persistent Frappe route wrapper when no `.layout-main-section` existed. Sales and Procurement create a single-column Frappe app page and mount managed content inside `page.body`, which Frappe 16.5 defines as the page-owned `.layout-main-section`.

The outer-wrapper mount bypassed the standard Page host geometry and allowed Finance-only trailing scroll space. The Finance shell itself has natural height and only 30px of intentional bottom padding; fixed height or overflow CSS was not the cause.

## Source correction

- Finance now creates one standard single-column Frappe Page when the route wrapper has no page.
- Repeated page-show calls reuse `wrapper.page`; they do not append another page head or body.
- Rendering resolves the jQuery-backed `page.body` to its DOM element.
- Wrapper resolution accepts only the supplied route wrapper. Global Page, descendant, outer-wrapper, and document-body fallbacks are removed. Missing or mismatched ownership fails closed before mount or RPC.
- Hide invalidation remains bound to the persistent outer route wrapper and is rebound if the owned Page body identity changes.
- Finance request, payload, accounting, role, permission, copy, focus, and live-region behavior is unchanged.

## Geometry proof

The pinned Docker smoke exercises the registered Finance page at 1366px, 390px, and 320px for manager-ready, Accounts User manager-only posture, non-Finance restricted, controlled unavailable, and transport-error states. The lifecycle fixture creates the Page through `make_app_page`, triggers the namespaced handler through the wrapper's runtime `hide` event, and proves return reuses the owned Page while loading fresh state.

The fixture models Frappe's `.main-section` as the viewport scroll owner and the standard Page body hierarchy. It proves exactly one Page creation, one managed presentation host, no horizontal overflow or overlap, no artificial scroll extent after the Finance shell, normal 30px shell bottom padding, reachable final content, natural long-content scrolling, and independent sidebar/content scrolling.

This is source-renderer evidence, not authenticated post-alignment browser acceptance.

## Source and live truth

Only the Finance page JavaScript intentionally differs from live after F6E4A:

- Source: `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`
  - SHA-256: `8f1d1839a95f23839305d8efd7a7d2f04e774b60d1f5ddcfa576528041a14fd9`
- Live currently remains at SHA-256: `d66cdae042761d1f2fcbc856c3521701a0757317dbeb3e4fa084203842bce2e5`

Finance service and shared sidebar remain source/live identical. Tests, smoke, README, and this document are source evidence and are not runtime-alignment files.

## Future controlled alignment

The exact future runtime-only allowlist is:

- `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`
  - Expected SHA-256: `8f1d1839a95f23839305d8efd7a7d2f04e774b60d1f5ddcfa576528041a14fd9`

No live alignment, restart, cache clear, metadata reload, migration, staging, commit, push, permission change, or protected gate occurred in F6E4A. F6F remains blocked until independent review, separately approved alignment, and authenticated Manager and Accounts User browser retests confirm the blank tail is gone without harming natural scrolling.
