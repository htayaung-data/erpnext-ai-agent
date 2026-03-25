# Qwen ERP Discovery Evidence Policy Note (2026-03-25)

Status: Mini-phase 4 boundary hardening  
Scope: make the discovery/runtime boundary explicit in metadata and discovery outputs

## 1. Why this exists

Discovery is now useful, but it still cannot prove business-meaning compatibility for most runtime-critical governed reports.

The main reason is structural:

1. most high-value governed reports are `Script Report`s
2. those reports expose little or no ERP-declared filter/column surface through the `Report` doc
3. so runtime still depends on governed semantic assumptions above discovery

This note records the corrective boundary:

1. discovery proves surface existence and some structural facts
2. curated evidence policy records what discovery does not prove
3. contracts stay responsible for semantic safety

## 2. New metadata layer

Added:

1. [report_surface_evidence_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_surface_evidence_registry.json)

This registry is intentionally narrow.

It does **not** replace:

1. report registry
2. capability registry
3. contracts

It only records for priority governed reports:

1. evidence class
2. what discovery proves
3. what discovery does not prove
4. which runtime assumptions are still curated
5. recommended runtime posture

## 3. Boundary rule

For these reports:

1. `Sales Analytics`
2. `Item-wise Sales History`
3. `Gross Profit`
4. `Sales Invoice List`
5. `Accounts Receivable`
6. `Accounts Payable`
7. `Balance Sheet`
8. `Profit and Loss Statement`
9. `Cash Flow`

the system now has an explicit evidence statement instead of silently treating governed metadata as if it were ERP-declared proof.

## 4. Enterprise effect

This improves governance in two ways:

1. discovery outputs are more honest
2. later runtime/contract work can read a structured evidence posture instead of inferring one ad hoc

## 5. What this does not do

This does not solve:

1. enrichment recovery UX
2. cross-report semantic compatibility
3. metric-union safety
4. fresh-query override after failed enrichment

Those remain later contract work.
