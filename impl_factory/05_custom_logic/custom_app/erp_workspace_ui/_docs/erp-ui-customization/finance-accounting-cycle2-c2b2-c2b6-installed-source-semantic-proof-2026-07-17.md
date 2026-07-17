# Finance & Accounting Cycle 2 C2B2-C2B6 Installed-Source Semantic Proof and Stop Receipt

**Main Control authority:** Main Control v2

**Parent plan:** [Finance & Accounting Cycle 2 GL / Trial Balance Scope and Implementation Plan](finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md)

**Accepted governance profile:** [Finance & Accounting Cycle 2 C2A2-C2A5 Scope and Governance Profile](finance-accounting-cycle2-c2a2-c2a5-scope-governance-profile-2026-07-17.md)

**Installed-source authority:** [Finance & Accounting Cycle 2 C2B1 Exact Installed-Source Fingerprint Receipt](finance-accounting-cycle2-c2b1-exact-installed-source-fingerprint-receipt-2026-07-17.md)

**Owner gate received:** `finance_cycle2_gl_tb_c2b2_c2b6_source_semantic_proof_authorized`

**Decision:** `c2b2_c2b6_semantic_proof_stopped_for_evidence_backed_control_gaps`

**Evidence timestamp:** `2026-07-17T10:00:09Z`

**State:** C2B3 and the bounded C2B5 posture close; C2B2, C2B4 and C2B6 stop; C2B7 and runtime remain unapproved

## 1. Outcome

The approved read-only C2B2-C2B6 pass completed against only the 69 files frozen by C2B1. It established the installed native formulas and a narrow base-currency/default-Finance-Book/no-dimension posture, but it also found evidence-backed accounting-control, permission-equivalence, closing-cache and consistency gaps. Consequently, this is a stop receipt rather than C2B source-proof closure.

| Mini-phase | Decision | Bounded result |
| --- | --- | --- |
| C2B2 GL Entry lifecycle | `stopped_for_gl_lifecycle_gap` | Core stored-row and cancellation semantics are mapped, but a concrete cancellation freeze-call mismatch and uninspected posting-admission dependencies prevent closure. |
| C2B3 Trial Balance algorithm | `closed_boundedly_for_algorithm_semantics` | Opening, movement, closing, netting, hierarchy and total-row formulas are mapped. The installed report is an internal semantic oracle only, not a safe adapter. |
| C2B4 fiscal and closing | `c2b4_stopped_for_pcv_cache_integrity_and_allowlist_dependency_gap` | Fiscal, PCV and Account Closing Balance paths are mapped, but completed-state, uniqueness, completeness and cache-to-GL parity are not enforced by the native consumer. |
| C2B5 Finance Book, currency and dimensions | `c2b5_closed_for_base_currency_company_default_book_no_dimension_slice_with_fail_closed_settings` | Only company base currency, resolved company-default book plus blank/NULL entries, and no dimension slice survive as a future contract candidate. |
| C2B6 permission, consistency and performance | `stopped_for_permission_and_consistency_proof_gaps` | Native Trial Balance and General Ledger reuse are rejected. A purpose-built aggregate-only reconstruction remains conditional and unselected. |
| C2B7 synthesis | Not started | No adapter is selected and no C2C or runtime authority is created by this receipt. |

## 2. Evidence boundary and containment

- Source repository remained `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`, branch `feature/erpnext-ui-design`.
- Pre-documentation `HEAD` and upstream were `aef907a530d825278d070c47237aa3041faced29`, ahead/behind `0/0`, with an empty index.
- Installed evidence was limited to the C2B1 manifest: 43 ERPNext v16.4.1 and 26 Frappe v16.5.0 files whose installed raw bytes match their accepted official references under canonical manifest digest `063f716c4138d6bf1f69ecf9e71b4f1bd9c0e5cb4118a5841aa2b5cc6de9d40c`.
- Static source text was parsed or read only. Installed application modules were not imported or invoked.
- No selected test files exist in the 69-file manifest. No runtime or behavioral-test claim is made.
- No database, site, report execution, DocType row, configuration value, log, secret, operational record, endpoint, browser, live deployment tree, migration, metadata, permission, cache, restart or accounting action was accessed or changed.
- A material dependency outside the 69-file manifest was named as a gap and not inspected.

## 3. C2B2 — GL Entry lifecycle proof

### 3.1 Field and lifecycle matrix

| Topic | Installed-source proof | Future contract posture |
| --- | --- | --- |
| Company and account | GL Entry stores `company` and `account`; controller validation requires the account to be a non-group, active account belonging to the same company. | One explicitly authorized company; malformed/cross-company rows fail closed. |
| Dates and fiscal year | `posting_date` is date-only. When absent, fiscal year is derived from posting date plus company. Creation/modified time is metadata, not the accounting-date basis. | Exact inclusive ISO dates; no timestamp reinterpretation; dates outside the approved fiscal context are rejected. |
| Opening state | `is_opening` is an explicit Yes/No marker. Profit-and-Loss opening entries are rejected by GL Entry validation unless cancelled. | Treat opening markers exactly; unsupported or malformed markers make the context unavailable. |
| Cancellation | Individual GL Entry cancellation is prohibited. Voucher cancellation flows through `make_reverse_gl_entries`. Native reporting normally reads `is_cancelled = 0`. | Never expose a mutation. Read only the proven eligible state and validate reversal posture. |
| Non-immutable cancellation | Originals are marked cancelled; swapped cancellation entries are also marked cancelled. Default reporting excludes both. | Exclude cancelled rows. |
| Immutable cancellation | Originals remain active and swapped active reversals are posted on the cancellation/current date. Both remain report-eligible and net through accounting amounts. | Preserve both rows; never deduplicate by voucher/account heuristics. |
| Voucher lineage | GL Entry carries voucher type/number/detail and against-voucher fields. | Use lineage only for internal reconciliation; never return it publicly. |
| Currency | Base, account, transaction and reporting-currency fields are present. Account/company currency validation and reporting-rate calculation occur during entry validation. | Initial candidate uses base debit/credit only; alternate currencies remain deferred. |
| Finance Book and dimensions | Finance Book, Cost Center, Project and dynamic dimensions participate in GL-map merge keys and stored rows. | Initial candidate uses explicit company-default book mode and no dimension slice. |
| Duplicate/malformed behavior | Similar GL-map entries may be merged by a defined key, but the selected sources prove no database composite-uniqueness or safe downstream deduplication rule. | Reject malformed rows and unexplained duplicates; do not infer uniqueness from voucher/account fields. |

Key selected-source locations are `erpnext/accounts/doctype/gl_entry/gl_entry.py:28-327`, `erpnext/accounts/doctype/gl_entry/gl_entry.json`, and `erpnext/accounts/general_ledger.py:274-355,680-831`.

### 3.2 High finding — cancellation freeze-call mismatch

The selected installed file contains a concrete call/signature mismatch:

- caller: `check_freezing_date(gl_entries[0]["posting_date"], adv_adj)` at `erpnext/accounts/general_ledger.py:715-716`;
- signature: `check_freezing_date(posting_date, company, adv_adj=False)` at `erpnext/accounts/general_ledger.py:792`.

The boolean `adv_adj` is therefore supplied as `company`, while the function's actual `adv_adj` parameter stays false. That function resolves `accounts_frozen_till_date` and the authorized frozen-entry role from the supplied company. The reversal later uses `make_entry` directly; GL Entry `on_update` checks a frozen account, not the company accounting freeze date. This is concrete evidence of a likely cancellation bypass of the company freeze-date control. The selected manifest contains no test covering this call, cancellation freezing, or immutable/non-immutable cancellation.

C2B2 stops. No runtime work may rely on the cancellation path until a separately authorized targeted source/test proof resolves the mismatch.

### 3.3 Material uninspected dependencies

The following imported or lifecycle-owning sources are outside the frozen manifest and were not read:

- `erpnext/accounts/party.py` for party admission and party-currency rules;
- `erpnext/accounts/doctype/budget/budget.py` and `erpnext/controllers/budget_controller.py` for posting-time budget admission;
- `erpnext/setup/utils.py` for reporting-currency exchange lookup;
- voucher controllers that construct GL maps, including Journal Entry, invoice, payment and stock-origin lifecycles.

These gaps prevent a complete end-to-end posting-admission claim. They do not authorize an allowlist extension.

## 4. C2B3 — Trial Balance algorithm proof

### 4.1 Exact installed algorithm

| Component | Installed behavior |
| --- | --- |
| Account set | Accounts are loaded for the requested company and ordered by nested-set `lft`; hierarchy is rebuilt and children accumulate into parents. |
| Opening | Uses eligible pre-`from_date` GL values, with explicit opening-entry rules, or the latest earlier submitted PCV's Account Closing Balance plus subsequent GL delta. |
| Movement | Uses eligible GL rows from `from_date` through `to_date`, normally excluding opening entries, grouped by account. |
| Closing | `closing_debit = opening_debit + period_debit`; `closing_credit = opening_credit + period_credit`. |
| Net view | For opening/closing display, Asset, Equity and Expense are debit-normal; Liability and Income are credit-normal. Negative net posture is moved to the opposite side. |
| Hierarchy and totals | Child values accumulate into parents in reverse order; the total row sums root accounts. |
| Zero filtering | Rows below the currency zero cutoff may be hidden while required ancestors remain; optional group-account hiding does not change calculations. |
| Root/category semantics | Native roots include Asset, Liability, Equity, Income and Expense, but public category summaries remain deferred until sensitive-account and completeness policy is approved. |
| Filters | Company, cancellation, dates, Finance Book, Cost Center, Project and configured accounting dimensions affect the source set. |

Selected-source anchors are `erpnext/accounts/report/trial_balance/trial_balance.py:34-565` and `erpnext/accounts/report/financial_statements.py:161-647`.

The signed invariant remains a future exact-Decimal contract:

```text
(opening_debit - opening_credit)
+ (period_debit - period_credit)
= (closing_debit - closing_credit)
```

Native `flt` arithmetic and a native report's visible result are not accepted as authoritative equality proof.

### 4.2 Native reports rejected as public adapters

- Trial Balance opening-account selection uses permission-bypassing `frappe.db.get_all`; the direct opening query runs without the GL movement path's `build_match_conditions`.
- Trial Balance returns account identifiers, names and numbers.
- General Ledger returns ledger identifiers, accounts, parties, vouchers, against-voucher data and optional remarks. It also loads party names using `get_all` and supplier invoice data through raw SQL.
- Trial Balance silently clamps out-of-fiscal-year dates; the accepted Cycle 2 contract requires rejection.
- Neither selected report contains the required fail-closed malformed-row, exact-Decimal, complete-chart, balanced-total or payload-identity assertions.

C2B3 closes only for the installed formula narrative. Native Trial Balance and General Ledger execution remain rejected.

## 5. C2B4 — fiscal, closing and reopening proof

| Scenario | Selected-source result | Required posture |
| --- | --- | --- |
| Fiscal-year bounds | Trial Balance rewrites dates outside the chosen fiscal year to the year boundary after a message. | Reject invalid context; never inherit silent clamping. |
| Mid-year start | Opening is calculated before `from_date`; a prior PCV cache may seed opening and later GL fills the gap. | Exact, documented as-of policy; no unexplained partial opening. |
| Opening and prior-year P&L | Settings and report filters alter opening-marker and unclosed prior-year P&L treatment. | Record the exact semantic settings; unsupported combinations return unavailable. |
| PCV selection | Native Trial Balance selects the latest earlier submitted PCV by company/date/docstatus. | Submission alone is insufficient. Require one uniquely selected completed PCV. |
| PCV lifecycle | Selected sources expose legacy and queued states including In Progress, Queued, Running, Paused, Completed, Failed and Cancelled. | Consume no PCV/ACB cache unless processing is Completed. |
| ACB construction | Closing balances aggregate by company, account, currencies, Cost Center, Project, Finance Book, PCV flag and active dimensions. | Prove complete key coverage and exact dimension basis. |
| Completeness and duplicates | The native Trial Balance consumer does not prove cache uniqueness, complete account/dimension coverage or rerun safety. | Missing, duplicate or ambiguous rows make the result unavailable. |
| Cache-to-GL parity | No selected consumer reconciles the ACB cache to authoritative GL before using it. | Require parity or reconstruct from a separately approved GL source. |
| Accounting Period | Posting hooks can block configured documents during a closed Accounting Period. | This is a posting control, not proof that reporting is closed, complete or audited. |
| Freeze and later postings | General ledger code has company freeze-date and PCV-date checks, but the cancellation mismatch and later/repost lifecycles prevent a blanket claim. | Detect context change and fail closed; do not label the result closed or certified. |

Material sources outside the frozen manifest were named but not inspected:

- `erpnext/accounts/doctype/process_period_closing_voucher_detail/process_period_closing_voucher_detail.py` and its metadata;
- `erpnext/controllers/accounts_controller.py`;
- `frappe/utils/scheduler.py`;
- `erpnext/setup/utils.py` for reporting exchange-rate behavior;
- the hook/event registration source for `period_closing_doctypes`.

C2B4 stops until an exact extension and targeted integrity proof are separately approved.

## 6. C2B5 — bounded financial context

The following narrow candidate is source-proven; it is not yet a public contract or adapter selection.

| Context element | Bounded accepted posture | Fail-closed/deferred posture |
| --- | --- | --- |
| Company | One resolved authorized company. | Missing, ambiguous or cross-company context is unavailable. |
| Currency | Company base currency using GL Entry `debit` and `credit`. | Account, transaction, presentation and reporting currencies are deferred. |
| Precision | Future Decimal quantization from an authoritative currency/System Settings contract. | Native `flt`, unknown precision/fraction units or invalid-to-zero coercion cannot prove equality. |
| Finance Book | `company_default`: resolved company default plus blank/NULL unbooked entries. | Default-only, selected non-default, blank-only and implicit all-books modes are unsupported. |
| Finance Book parity | Opening and movement must resolve the identical inclusion rule. | Missing default or any opening/movement divergence is unavailable. |
| Cost Center | No slice. Installed filtered behavior includes descendants. | Cost Center slices are deferred. |
| Project | No slice. Installed filtered behavior is exact membership. | Project slices are deferred. |
| Custom dimensions | No slice; active dimensions may still participate in PCV/ACB grouping. Tree filters include descendants. | Custom-dimension slices and unknown active metadata are deferred/unavailable. |

A selected-source High remains: Trial Balance applies opening Finance Book filtering only when Finance Book records exist, while current movement applies its filter unconditionally. Future reconstruction must prove identical opening/movement book scope before returning ready.

C2B5 closes only for the narrow posture above and with all stated settings resolved fail closed.

## 7. C2B6 — permission, completeness, consistency and adapter posture

### 7.1 Permission call-graph result

```text
Query Report role/ref-DocType gate
  -> execute native Trial Balance script
     -> Account chart via raw SQL
     -> PCV selection via permission-bypassing get_all
     -> opening via raw Query Builder
     -> movement via a separate path with GL match conditions
     -> hierarchy accumulation and totals
  -> post-filter returned Link-column values only
```

The post-filter occurs after calculation and cannot retroactively permission-scope opening, movement, hierarchy or totals. Selected Frappe source explicitly shows `get_all` setting `ignore_permissions=True`; raw Query Builder does not automatically establish the `DatabaseQuery` permission path.

### 7.2 Evidence-backed blockers

1. **Opening and movement are not permission-equivalent.** Direct opening/account/PCV/dimension reads differ from the permission-conditioned movement path.
2. **Report and PCV roles conflict.** Trial Balance metadata permits Accounts User, Accounts Manager and Auditor; Period Closing Voucher metadata grants read only to System Manager and Accounts Manager. Trial Balance still reads PCV data through `get_all`.
3. **Complete-chart authority is unproven.** Post-filtered report output cannot prove that every account participating in a balanced assertion was authorized and included.
4. **Coherent snapshot is unproven.** The report performs multiple dependent reads without an explicit report-level snapshot or change-detection contract.

### 7.3 Performance and service boundary

- The native reports provide no capability-specific account, row, query, time, memory or response-size caps.
- Page permission governs navigation, not a future whitelisted service. A service must separately enforce authentication, role purpose, company, DocType, field and User Permission gates before financial reads.
- A future safe candidate must use permission-preserving reads, exact company/account/dimension authority, no identities or rows, fixed caps, exact Decimal arithmetic, and a proven snapshot or reconciliation token.
- If any Account or dimension restriction prevents complete-chart authority, the service must return unavailable rather than a visible-subset result labelled balanced.

### 7.4 Adapter disposition at this gate

| Candidate | C2B2-C2B6 disposition |
| --- | --- |
| Native General Ledger | Rejected: identity-rich, permission-bypassing auxiliary reads, rows/vouchers/remarks and no aggregate-only contract. |
| Native Trial Balance / Query Report passthrough | Rejected: non-equivalent opening/movement permissions, post-calculation filtering, role mismatch, date clamping and float arithmetic. |
| Reuse native ACB/opening calculation | Rejected unless a later proof establishes completed PCV, cache completeness/uniqueness/parity and identical permissions/snapshot. |
| Purpose-built aggregate-only reconstruction | Conditionally viable, not selected: requires C2B gap closure and later C2C contract approval. |

Runtime-only evidence still unavailable and uninspected includes effective Custom DocPerm/Custom Field/Property Setter and permission hooks; actual User Permission and strict-permission settings; active dimension definitions/tree values; deployed database isolation/replica behavior; current company/fiscal/book/closing state; and enforced query/time/memory/payload limits.

C2B6 stops. C2B7 may not begin from this receipt.

## 8. Findings by severity

| Severity | Finding | Evidence/disposition |
| --- | --- | --- |
| Blocker | Native Trial Balance opening, movement, account, PCV and dimension paths are not permission-equivalent. | Selected ERPNext/Frappe source; reject native reuse. |
| Blocker | Trial Balance can consume submitted PCV/ACB data without requiring Completed processing, completeness, uniqueness or GL parity. | Selected Trial Balance, PCV and ACB source; C2B4 stops. |
| Blocker | Query Report post-filtering cannot prove complete-chart authority or a balanced aggregate. | `frappe/desk/query_report.py`; C2B6 stops. |
| High | Cancellation freeze-date call supplies `adv_adj` where `company` is required. | Exact caller/signature mismatch in selected `general_ledger.py`; C2B2 stops pending targeted proof. |
| High | Native GL exposes account/party/voucher identities and uses bypassing auxiliary reads. | Selected GL report and Frappe `get_all`; native GL remains oracle-only. |
| High | Native float behavior and unknown runtime precision cannot prove exact equality. | Selected Trial Balance/Frappe utility behavior; require later Decimal contract. |
| High | Finance Book opening and movement inclusion can diverge. | Selected Trial Balance/financial-statements paths; bounded C2B5 close only. |
| High | No report-level snapshot or complete-chart permission proof exists. | Selected query/report/database paths; later runtime evidence required. |
| Medium | Native fiscal-date clamping conflicts with the accepted strict-rejection contract. | Selected Trial Balance filter validation; custom contract must reject. |
| Medium | No selected tests or native capability-specific workload caps exist. | Frozen manifest and selected reports; no behavioral/performance closure claim. |

## 9. One-pass independent review disposition

| Review | Disposition |
| --- | --- |
| Accounting lifecycle and algorithm | Accepted the C2B2 stop and bounded C2B3 formula closure. Accepted the freeze-call mismatch as High because the exact selected caller/signature proves it. |
| Fiscal, closing, currency and dimensions | Accepted the C2B4 stop and bounded C2B5 posture. No native cache-integrity claim survives. |
| Security, permissions and leakage | Accepted the C2B6 blockers and native-report rejection. No identity-bearing report path is approved. |
| Cross-workspace and Shared UI | No source or runtime surface changed, so no protected-workspace or Shared UI gate was triggered. Existing boundaries remain intact. |
| Architecture and release containment | Accepted stop before C2B7. Controlled reconstruction remains a hypothesis only. No repeated review loop was opened. |

No Blocker or High was accepted without exact selected-source evidence. No evidence-backed finding was rejected. Runtime-only questions are deferred rather than inferred.

## 10. Phase authority and next Owner decision

| Phase | State after this receipt |
| --- | --- |
| C2A1-C2A5 | Complete and published. |
| C2B1 | Closed for the frozen 69-file manifest. |
| C2B2 | Stopped. |
| C2B3 | Bounded algorithm-semantics close; native adapter rejected. |
| C2B4 | Stopped. |
| C2B5 | Bounded context close only. |
| C2B6 | Stopped. |
| C2B7 | Not started and not authorized. |
| C2C-C2E | Not started and not authorized. |

Before C2B7 can be proposed, the Owner must separately choose whether to authorize a **targeted C2B gap-closure plan**. That future planning gate would define, without inspecting anything yet:

1. an exact fingerprint extension for only the material lifecycle/PCV/permission dependencies;
2. a bounded behavioral proof for the cancellation freeze-call mismatch;
3. PCV Completed-state, ACB completeness/uniqueness/cache-to-GL parity evidence;
4. an allowed metadata/config-only permission and consistency evidence boundary, or an explicit decision that those contexts must remain unavailable;
5. exact tests, one-pass counterpart review and stop conditions.

This receipt does not itself authorize that extension or proof.

## 11. Documentation candidate and exclusions

The exact future documentation staging candidate is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

The four unrelated exclusions remain outside the candidate and must remain untouched and unstaged:

| Path | Required status and SHA-256 |
| --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | Modified, unstaged; `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | Untracked; `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | Untracked; `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | Untracked; `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

No staging, commit, push, live alignment, protected gate or runtime action is implied.
