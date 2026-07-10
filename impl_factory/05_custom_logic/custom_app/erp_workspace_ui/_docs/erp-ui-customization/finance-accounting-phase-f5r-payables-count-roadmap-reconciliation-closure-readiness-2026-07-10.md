# Finance & Accounting Phase F5R - Payables Count-Only Roadmap Reconciliation / Closure Readiness

Date: 2026-07-10
Status: stopped gap report; controlled staging review is not ready
Workspace family: Finance & Accounting
Page label: Finance Control Desk
Finance AR baseline: `e198fa4aaca77c7ed2f65c98256644b20e7bbeb0`

## Decision

The current live `payment_terms_not_supported` result is accepted as a safe controlled-unavailable state, but the Finance F5 Payables source package is not ready for controlled staging review.

The source runtime detects `payment_terms_template` but cannot prove that a Purchase Invoice has no template-less Payment Schedule child rows. On different data, that gap could permit a ready voucher-level count that does not represent schedule-level obligations. F5R does not implement Payment Schedule support under its hard boundary. No files were staged, committed, pushed, or live-aligned by F5R.

## Roadmap Truth

The initial F5 design was a proposal, not a record of completed work. Later operational labels reused `F5D` and `F5E` for count-only review activities. The following table preserves both histories without claiming that amount work exists.

| Label | Original F5 plan | Actual completed work | Closure truth |
| --- | --- | --- | --- |
| F5 | Payables posture policy/design | Docs-only business, role, source-risk, UI, and boundary policy | Completed |
| F5A | Payables visibility/source policy | Docs-only accepted/rejected source policy and count semantics | Completed |
| F5B | Role/company/currency gate contract | Installed-source proof and count contract, including role/company gates and fail-closed rules | Completed for count-only policy; no amount proof |
| F5C | AP count-only posture | Accounts Manager-only aggregate Purchase Invoice count posture implemented with no rows or amounts | Completed source implementation |
| F5C1 | Not in the original table | Counterpart review found no Blocker or High issue; Payment Schedule caveat remained | Completed review; standalone artifact was not created |
| F5C2 | Not in the original table | Caveat documentation and business-facing unavailable/current-not-overdue copy | Completed source/docs polish |
| F5D | Manager-only AP amount source proof | Operational label reused for count-only live alignment for manual review | Live alignment completed; original amount proof not performed |
| F5D1 | Not in the original table | Live diagnostic proved manager/company/Purchase Invoice permission gates pass and `payment_terms_not_supported` causes controlled unavailable | Completed diagnostic; standalone artifact was not created; no patch |
| F5E | Manager-only AP amount runtime | Operational label reused for the count-only manual acceptance artifact | Manual acceptance recorded; original amount runtime not performed |
| F5F | Manual review/live decision | Count-only manual review outcome is represented by F5D, F5D1, and F5E | Count-only review completed; no amount review |
| F5G | Hardening/closure | F5R performs grouped reconciliation and closure-readiness review | Stopped on template-less Payment Schedule proof gap |

The missing standalone F5C1/F5D/F5D1 artifacts are a release-traceability limitation. F5R records their accepted outcomes without pretending that absent command transcripts or artifacts exist.

Future AP amount work must not reuse this table as evidence of approval. It requires a newly approved source-policy/proof phase and a separately approved runtime phase.

## Completed Count-Only Posture

The current source candidate contains:

- one compact Payables posture lane in Finance Control Desk;
- `Accounts Manager` as the only role eligible for AP aggregate counts;
- Finance resolver-selected company scope for `Mingalar Mobile Distribution Co., Ltd.` / `MMK`;
- permission-preserving Purchase Invoice aggregate count reads through `frappe.get_list`;
- due-date-only current/not-overdue and overdue count buckets;
- strict aggregate parsing;
- fail-closed handling for missing due date, future-posted invoices, detected payment terms template, on-hold invoices, returns/debit notes, wrong company, permission denial, and malformed source output;
- no adapter call for `Accounts User` or non-Finance roles;
- frontend raw/nested payload guards for row, identity, native surface, and action-shaped data;
- controlled unavailable copy that does not show internal policy reason codes to normal users.

## Accepted Fail-Closed Live State

The live manager result `payment_terms_not_supported` is accepted because at least one open Purchase Invoice has a payment terms template and the first count model does not interpret Payment Schedule child rows. The response returns no count buckets after this condition is detected.

This unavailable result is safer than presenting potentially incomplete or incorrectly aged AP buckets. It is not an AP aging total, AP balance, cash requirement, payment authority, supplier worklist, or native Accounts Payable report.

The resolver used `single_company_site_fallback` for `Mingalar Mobile Distribution Co., Ltd.`. Owner acceptance of this fallback is limited to the current single-company F5 count-only scope. It does not authorize multi-company Finance data or grant Company/accounting permissions.

## Deferred

The following remain separate future work:

- Payment Schedule child-row source policy and proof, including schedules without a payment terms template;
- manager-only AP amount source proof;
- company-currency-safe payable voucher-outstanding semantics;
- manager-only AP amount runtime and low-population suppression;
- Accounts User count coarsening or suppression policy;
- supplier, Purchase Invoice, Payment Entry, account, voucher, Payment Ledger Entry, and GL Entry rows or identities;
- native Accounts Payable reports, Form/List/query-report routes, exports, downloads, and print;
- payment preparation worklists, payment runs, bank/cash integration, and accounting execution.

## Closure-Blocking Finding

A Purchase Invoice may contain Payment Schedule child rows without `payment_terms_template`. The current F5C gate checks only the template field and does not read child schedule rows. This was documented as a residual caveat in F5C2, but closure review correctly distinguishes a documented caveat from proof that a general ready result is safe.

The currently observed live invoice does contain a payment terms template, so the live result remains safely unavailable and accepted. The unresolved case affects source-package staging readiness on other or future data.

F5R does not patch this gap because Payment Schedule source reads and interpretation are explicitly outside scope. Reopen it through a separate Payment Schedule source-policy/proof phase. Until then, the current live controlled-unavailable result may remain accepted, but the package must not be described as generally closure-ready.

## High Finding Remediated In F5R

F5R found that future-posted open Purchase Invoices were not gated against the server-derived `as_of` date. The narrow remediation adds an aggregate fail-closed check for `posting_date > as_of_date`. It returns unavailable with no bucket counts and does not read or expose source rows.

## Independent Closure-Readiness Review

Four bounded read-only review tracks were used. They were advisory and performed no edits or operational actions.

Accounting/AP semantics:

- accepted the controlled-unavailable result as safer than incorrect payment-schedule aging;
- confirmed that count-only Purchase Invoice posture is operational visibility, not an AP balance or amount truth;
- identified template-less Payment Schedule detection as a staging-readiness blocker;
- identified and prompted the remediated future-posting-date fail-closed gap.

Security/data leakage:

- confirmed manager/company/source-permission gates and denied-role early exits;
- confirmed current Payables payloads contain aggregate count buckets only when ready and no source rows or identities;
- confirmed native navigation, external output, and execution flags remain disabled;
- noted that a future hardening phase should prefer a Payables-specific exact response schema; current server payload remains count-only.

Test/release governance:

- confirmed focused tests cover manager readiness, denied roles, selected company, permission errors, detected fail-closed complexity, malformed aggregates, safe response shape, and frontend guard keys;
- identified missing standalone F5C1/F5D/F5D1 evidence and retained that as a traceability limitation rather than inventing history;
- classified every current dirty path as include or exclude below;
- requires exact-path staging and a fresh staged diff/boundary review after the blocker is resolved.

Shared UI/UX:

- confirmed Accounts User sees manager-only business wording rather than `accounts_manager_required`;
- confirmed manager-ready copy defines current/not overdue as due today or later;
- confirmed unavailable posture has no active payment, report, export, or document controls;
- noted that the generic unavailable message and static `Count-only` readiness row should be polished in a later narrow UI task so the visible reason is clearer without exposing internal codes.

## Exact Future Staging Candidate After Blocker Resolution

After the Payment Schedule proof blocker is resolved and the package is re-reviewed, a future controlled staging review may include exactly these paths:

- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-phase-f5-payables-posture-policy-design-2026-07-09.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-phase-f5a-payables-visibility-source-policy-2026-07-09.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-phase-f5b-payables-source-proof-count-contract-2026-07-09.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-phase-f5c2-payables-count-caveat-documentation-ui-copy-polish-2026-07-09.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-phase-f5e-payables-count-manual-browser-acceptance-2026-07-10.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-phase-f5r-payables-count-roadmap-reconciliation-closure-readiness-2026-07-10.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/finance_accounting/service.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_accounting_payables_count.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_accounting_shell.py`

These paths are classified candidates only. F5R does not approve or perform staging.

## Explicit Exclusions

These dirty paths are unrelated to the accepted Finance F5 package and must remain unstaged:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

No other dirty path is unclassified at F5R.

## Source And Live Drift Awareness

F5D copied the accepted Finance service, Finance Control Desk page, focused Finance tests, F5 docs, and README to the live mirror, then ran the separately approved minimal backend/cache actions. F5D validation recorded matching source/live checksums for the copied runtime files, and F5D1 diagnosed the browser-facing method in the live backend.

F5R now contains a source-only future-posting fail-closed remediation and new F5E/F5R docs that are not live-aligned. Source and live therefore intentionally differ after F5R. A future staging, commit, or deployment decision must recheck source status, staged scope, and source/live checksums rather than assuming agreement.

## Not Approved

F5R does not approve staging, commit, push, protected gates, live alignment, restart, cache clear, metadata reload, migration, user/role/permission/DocType mutation, payment-schedule implementation, AP amounts, rows, native ERP surfaces, payment/accounting mutation, notification, email, portal, supplier communication, or any external action.

## Recommended Next Step

Open a separate Payment Schedule source-policy/proof phase. It must prove permission-preserving detection and safe fail-closed behavior for template-less schedules without returning supplier or invoice identities. Do not weaken the current `payment_terms_not_supported` gate, and do not stage the F5 package until closure readiness is re-reviewed.
