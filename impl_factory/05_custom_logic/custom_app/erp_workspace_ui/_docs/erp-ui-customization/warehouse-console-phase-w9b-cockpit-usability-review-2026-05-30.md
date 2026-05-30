# Warehouse Console Phase W9B Cockpit Usability Review

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: docs-only control-agent usability review. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

## 1. Baseline Reviewed

Accepted baseline before this review:

- W9 docs-only information architecture plan: `5e48154b5caae89988b3ecec932294bee806156d`
- W9A runtime implementation: `97b7f063a8ec9f248e6aaea63a8b5f4444f68336`
- W9A baseline documentation: `3aa818a3c8d442ee1b0b64951ec6cf4f2a6910f3`

Accepted W9A artifacts reviewed:

- Source W9A cockpit smoke: `/tmp/warehouse-phase-w9a-source-20260530T054904Z/warehouse-w9a-cockpit-20260530T054911Z/warehouse-w9a-cockpit-summary.json`
- Source protected gate: `/tmp/warehouse-phase-w9a-protected-source-20260530T055502Z/protected-workspace-gate-summary.json`
- Live source/hash proof: `/tmp/warehouse-w9a-live-hashes-20260530T061504Z.txt`
- Live W9A cockpit smoke: `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-w9a-cockpit-summary.json`
- Final protected live gate: `/tmp/warehouse-phase-w9a-protected-live-20260530T063811Z/protected-workspace-gate-summary.json`

Accepted W9A live screenshots reviewed:

- `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-manager-desktop-1440-cockpit.png`
- `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-manager-laptop-1136-cockpit.png`
- `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-manager-mobile-390-cockpit.png`
- `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-user-desktop-1440-cockpit.png`
- `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-user-laptop-1136-cockpit.png`
- `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-user-mobile-390-cockpit.png`

## 2. Review Decision

W9A is accepted as a protected Warehouse cockpit baseline. W9B should not immediately send another implementation task to the Warehouse agent.

Recommended next step: hold W9A as the current Warehouse landing baseline and perform owner visual walkthrough on the live cockpit before W8C Transfer Visibility.

Reason:

- W9A made the landing surface substantially clearer.
- The cockpit now answers the correct operational questions: what to review, what risk exists, and what movement already happened.
- The current implementation stays inside the protected route model and does not introduce a new operational domain.
- The remaining issues are polish and evidence-quality items, not blockers.

Do not start W8C implementation until the owner either accepts W9A cockpit usability or explicitly prioritizes transfer visibility over landing refinement.

## 3. What Is Working

W9A has the right high-level information architecture:

- The cockpit starts with a clear Warehouse Console purpose statement.
- The read-only status is visible before any operational cards.
- Warehouse Pulse compresses the current posture into six quick checks.
- Start Here gives priority actions without adding Quick Find/Search.
- Work To Do pairs inbound receiving and outbound picking, which matches daily warehouse attention.
- Risks To Resolve keeps stock exceptions and stock posture framed as review work, not execution.
- Movement To Understand separates posted movement visibility from stock execution.
- The guardrail footer reinforces that stock updates stay in controlled ERP operations.

The live smoke summary confirms:

- Warehouse Manager and Warehouse User both passed.
- No console errors, page errors, failed responses, or failed requests were recorded.
- Single Warehouse shell/header rendering was preserved.
- Search utility was not visible.
- Horizontal overflow was zero in captured states.
- The cockpit had six pulse cards, four Start Here cards, two Work To Do cards, two risk cards, two movement cards, and one guardrail on accepted laptop/mobile cockpit captures.

## 4. Usability Gaps To Track

These are not release blockers, but they should guide the next Warehouse polish decision.

### 4.1 Desktop Evidence Gap

The live W9A `1440` screenshots labeled `cockpit` ended on `/desk/warehouse-console-worklist/movement-visibility` after route navigation.

This does not prove a runtime bug, because laptop and mobile captures show the cockpit and the smoke state asserts route behavior. It does mean the evidence package is weaker than it should be for a premium cockpit review.

Future cockpit smoke should capture two screenshot classes:

- `cockpit-initial` before any Start Here or route navigation.
- `route-drilldown-final` after clicking each protected start.

This keeps visual acceptance evidence aligned with the filename and makes owner review faster.

### 4.2 Mobile Density

The mobile cockpit is functional and has no horizontal overflow, but it is dense:

- Six Warehouse Pulse cards appear before the user reaches Start Here.
- Start Here is below the first screen.
- Long freshness timestamps consume attention.
- Repeated action buttons appear in Start Here and later sections.

Recommended future polish:

- Compress Warehouse Pulse to four primary cards on mobile.
- Move freshness into a compact caption or one status chip.
- Keep Start Here closer to the first viewport.
- Consider collapsing lower-priority detail previews behind section-level cards on narrow screens.

### 4.3 Priority Language

The current labels are safe and understandable, but some copy still reads like a system summary rather than a warehouse supervisor cockpit.

Examples to review in a future visual-polish pass:

- `Receiving attention` could become `Inbound needs review`.
- `Picking attention` could become `Outbound needs review`.
- `Movement records` could become `Recent posted movements`.
- `Warehouse posture` could become `Locations in view`.

Any copy change must keep the read-only boundary explicit and avoid lifecycle/action verbs such as receive, post, transfer, reconcile, reserve, dispatch, submit, approve, or close.

### 4.4 Percent Values Need Meaning

The Work To Do previews show percentages on inbound and outbound rows. The values are useful only if the label is obvious.

Recommended future polish:

- Label percentages as `received`, `pending`, `coverage`, or another explicit operational meaning.
- Avoid unlabeled percentage-only metadata in premium rows.
- Keep percentage labels non-financial and non-valuation.

### 4.5 Repeated Action Buttons

The same protected starts appear in Start Here and in the lower Work/Risk/Movement sections.

This is acceptable for discoverability, but it can create visual repetition. Future polish should choose one of these patterns:

- Keep Start Here as the only prioritized action launcher and make lower sections informational.
- Keep lower section action buttons and make Start Here a compact ordered task strip.

Do not add a generic search field to solve this repetition.

## 5. Protected Boundaries For Any W9B Polish

If an implementation pass is later approved from this review, it must remain W9B polish only.

Allowed:

- Cockpit layout refinements.
- Copy refinements.
- Visual density improvements.
- Mobile stacking improvements.
- Smoke screenshot evidence hardening.
- Existing W9A source smoke strengthening.
- Existing protected route starts only.

Forbidden:

- New Warehouse backend methods.
- New Warehouse route families.
- W8C Transfer Visibility.
- Native ERPNext form, list, report, or workspace route targets.
- Warehouse Quick Find/Search.
- Stock Entry, Purchase Receipt, Delivery Note, Pick List, Stock Reconciliation, reservation, transfer, or lifecycle controls.
- Stock mutation or stock posting.
- Valuation, accounting, GL, commercial, rate, amount, margin, profit, cost, tax, billing, payment, or landed-cost exposure.
- Sales runtime changes.
- Procurement runtime changes.

## 6. Recommended Assignment Split

Main control agent responsibilities:

- Keep W9B as docs-only unless owner approves an implementation pass.
- If implementation is approved, write a narrow Warehouse-agent prompt limited to cockpit polish and smoke screenshot hardening.
- Run credentialed focused Warehouse smoke, Sales freeze, protected source gate, commit/push, live alignment, live smoke, protected live gate, and baseline docs after Warehouse agent returns source-only changes.

Warehouse agent responsibilities only after an approved prompt:

- Implement W9B cockpit polish in source only.
- Strengthen W9A/W9B smoke screenshot evidence if requested.
- Run non-credentialed source validation.
- Stop before commit, push, or live alignment.

Owner responsibilities:

- Review the live W9A cockpit visually.
- Decide whether W9B polish is needed or whether W8C Transfer Visibility should be planned next.

## 7. Decision Options

Recommended option: owner visual acceptance first.

Option A: Accept W9A and move to W8C docs-only Transfer Visibility plan.

- Best if the owner is satisfied with the cockpit and needs transfer posture next.
- Keeps execution out of scope until W8C design is documented and accepted.

Option B: Run W9B implementation polish.

- Best if the owner wants a more premium landing surface before more Warehouse capability.
- Should focus only on mobile density, copy, screenshot evidence, and visual hierarchy.
- No new route or backend capability.

Option C: Pause Warehouse implementation for a counterpart review.

- Best if there is concern that the Warehouse surface has grown too quickly.
- Review should audit route ownership, no-native-escape controls, read-only boundaries, valuation exclusion, Sales/Procurement protection, and smoke evidence quality.

## 8. Recommended Next Prompt If Owner Chooses W9B Implementation

Use this only if the owner explicitly chooses W9B implementation polish:

```text
You are the Warehouse implementation agent. Implement W9B source-only cockpit usability polish for the protected Warehouse Console.

Scope:
- Work only in the source repo at `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`.
- Preserve existing accepted routes. Do not add backend methods or route families.
- Improve `/desk/warehouse-console` cockpit usability only:
  - make Start Here more prominent, especially on mobile;
  - reduce mobile density;
  - clarify unlabeled percentage metadata in Work To Do rows;
  - tighten owner-facing copy while preserving read-only language;
  - avoid repeated visual noise where safe;
  - harden W9A/W9B smoke screenshot evidence by capturing `cockpit-initial` before route navigation and `route-drilldown-final` after protected route starts.

Hard exclusions:
- No Warehouse Quick Find/Search.
- No native ERPNext form/list/report/workspace links.
- No Stock Entry/Purchase Receipt/Delivery Note/Pick List/Stock Reconciliation/reservation/transfer execution.
- No lifecycle verbs/actions: receive, post, submit, cancel, amend, transfer, reconcile, reserve, dispatch, close, approve, reject.
- No valuation/accounting/commercial fields or copy.
- No Sales runtime changes.
- No Procurement runtime changes.

Validation required before handoff:
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched Warehouse runtime JS and smoke files
- `python3 -m json.tool ui_smoke/package.json`
- `bash -n ui_smoke/run_playwright_docker.sh`
- `git diff --check HEAD`
- static scans for native escape, mutation/lifecycle controls, valuation/accounting/commercial exposure, Quick Find/Search, and Sales/Procurement dirty boundary

Stop before commit, push, live alignment, or protected gates. Report changed files, validation results, final git status, and the exact credentialed focused smoke command for main control.
```

## 9. Main Control Recommendation

Do not send the implementation prompt yet unless the owner wants more cockpit polish now.

The better immediate control-agent action is to ask the owner to review the live W9A cockpit:

- Sign in as Warehouse Manager.
- Confirm `/desk` lands on `/desk/warehouse-console`.
- Review laptop/desktop width and mobile width if possible.
- Check whether Start Here is clear enough.
- Check whether Work To Do, Risks To Resolve, and Movement To Understand match the way warehouse staff think.

If accepted, proceed to a W8C docs-only Transfer Visibility plan.
