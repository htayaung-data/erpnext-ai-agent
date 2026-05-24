# V1-R-F Synthetic Dataset Manifest Template

Decision target: `v1_r_f_synthetic_dataset_manifest_template_ready_for_counterpart_qa_review`

## Scope

V1-R-F is a template-only/report-only slice. It defines a safe synthetic dataset manifest template for a future Smoke-10 browser UAT run.

This report does not create an actual `.json` manifest file, create seed/data files, write to ERP, create a site or user, run browser automation, capture screenshots, collect traces, edit source/test files, stage, commit, push, deploy, enable strict enforcement, or implement V2 work.

## Manifest Template Identity

| Field | Template value |
| --- | --- |
| Manifest name | `V1_BROWSER_UAT_SYNTHETIC_SET_001` |
| Manifest type | Browser UAT synthetic dataset template |
| Intended run scope | Smoke-10 scenarios only |
| Execution status | Not executable until owner/QA approve concrete values |
| Storage status | Markdown governance template only; no `.json` manifest created |

## Manifest Template

Future approved manifest content should follow this structure. Values shown here are safe synthetic placeholders only.

| Section | Required fields | Template values |
| --- | --- | --- |
| Identity | `manifest_name`, `approval_reference`, `owner`, `qa_reviewer` | `V1_BROWSER_UAT_SYNTHETIC_SET_001`, `TBD_OWNER_QA_APPROVAL`, `TBD_OWNER`, `TBD_QA_REVIEWER` |
| Site | `site_label`, `site_url`, `environment_type` | `TBD_NON_PRODUCTION_SITE_LABEL`, `TBD_NON_PRODUCTION_SITE_URL`, `non_production` |
| Context | `company`, `fiscal_year`, `date_context`, `currency` | `EC7H Synthetic Company`, `TBD_SYNTHETIC_FISCAL_YEAR`, `TBD_SYNTHETIC_DATE_CONTEXT`, `TBD_CURRENCY` |
| Customers | `customer_id`, `display_name`, `outstanding_balance`, `aging_bucket` | Clearly synthetic customer records only |
| Suppliers | `supplier_id`, `display_name`, `payable_balance`, `due_bucket` | Clearly synthetic supplier records only |
| Items/products | `item_id`, `display_name`, `sales_quantity`, `sales_amount` | Clearly synthetic item records only |
| Sales invoice | `invoice_id`, `customer_id`, `amount`, `status`, `due_date_context` | Clearly synthetic invoice ID only, e.g. `EC7H-SINV-0001` |
| AR summary | `top_customers`, `overdue_total`, `oldest_invoice_ref` | Synthetic AR records only |
| AP summary | `top_suppliers`, `overdue_total`, `upcoming_due_total` | Synthetic AP records only |
| P&L summary | `period`, `income_total`, `expense_total`, `profit_total` | Synthetic financial totals only |
| Sales summary | `top_customers`, `top_items`, `period` | Synthetic sales records only |
| Scenario mappings | `scenario_id`, `required_records`, `expected_dataset_status` | Smoke-10 mapping table below |

## Synthetic Record Templates

### Synthetic Customers

| Synthetic ID | Display name | Purpose |
| --- | --- | --- |
| `EC7H-CUST-A` | `EC7H Synthetic Customer A` | AR outstanding and sales performance |
| `EC7H-CUST-B` | `EC7H Synthetic Customer B` | AR comparison and ranking |
| `EC7H-CUST-C` | `EC7H Synthetic Customer C` | Follow-up/detail variation |

### Synthetic Suppliers

| Synthetic ID | Display name | Purpose |
| --- | --- | --- |
| `EC7H-SUP-A` | `EC7H Synthetic Supplier A` | AP payable summary |
| `EC7H-SUP-B` | `EC7H Synthetic Supplier B` | AP overdue comparison |

### Synthetic Items / Products

| Synthetic ID | Display name | Purpose |
| --- | --- | --- |
| `EC7H-ITEM-A` | `EC7H Synthetic Item A` | Sales/product performance |
| `EC7H-ITEM-B` | `EC7H Synthetic Item B` | Product comparison |

### Synthetic Invoice

| Synthetic ID | Display name | Purpose |
| --- | --- | --- |
| `EC7H-SINV-0001` | `EC7H Synthetic Sales Invoice 0001` | Invoice lookup/detail for `V1RA-033` |

`SINV-0001` is not valid by itself. The future manifest must use a clearly synthetic identifier such as `EC7H-SINV-0001` and must explicitly map it before execution.

### Synthetic Summary Records

| Summary record | Required synthetic content |
| --- | --- |
| AR summary | Synthetic outstanding balances for `EC7H Synthetic Customer A/B/C` |
| AP summary | Synthetic payable balances for `EC7H Synthetic Supplier A/B` |
| P&L summary | Synthetic income, expense, and profit totals for `EC7H Synthetic Company` |
| Sales summary | Synthetic sales totals by customer and item |
| Follow-up seed | A deterministic prior answer/context record for `V1RA-041` |
| Boundary seed | No real data required; expected policy/boundary behavior only |

## Smoke-10 Scenario Mappings

| Scenario ID | Scenario purpose | Required synthetic mapping | Missing mapping result |
| --- | --- | --- | --- |
| `V1RA-001` | AR/customer outstanding | `EC7H-CUST-A`, `EC7H-CUST-B`, AR summary | `uat_blocked_dataset` |
| `V1RA-009` | AP/supplier payable | `EC7H-SUP-A`, `EC7H-SUP-B`, AP summary | `uat_blocked_dataset` |
| `V1RA-017` | P&L/profit summary | `EC7H Synthetic Company`, P&L summary | `uat_blocked_dataset` |
| `V1RA-025` | Sales/customer performance | `EC7H-CUST-A`, `EC7H-CUST-B`, sales summary | `uat_blocked_dataset` |
| `V1RA-033` | Invoice lookup/detail | `EC7H-SINV-0001`, `EC7H-CUST-A`, invoice detail | `uat_blocked_dataset` |
| `V1RA-041` | Follow-up detail/explanation | Prior AR/customer answer context from `V1RA-001` or approved follow-up seed | `uat_blocked_dataset` |
| `V1RA-049` | Vague business overview | AR, AP, P&L, and sales summaries or expected clarification path | `uat_blocked_dataset` |
| `V1RA-055` | Messy/mobile AR shorthand | Same AR summary mapping as `V1RA-001` | `uat_blocked_dataset` |
| `V1RA-061` | Recommendation boundary | Boundary expectation; optional factual AR/sales alternative records | `uat_blocked_dataset` only if factual alternative required |
| `V1RA-064` | Write/action boundary | Boundary expectation; no write-capable record required | `uat_blocked_dataset` only if site lacks AI Assistant boundary route |

## Synthetic Naming Rules

Allowed naming patterns:

| Record type | Allowed pattern |
| --- | --- |
| Customer | `EC7H Synthetic Customer <Letter>` |
| Supplier | `EC7H Synthetic Supplier <Letter>` |
| Item/product | `EC7H Synthetic Item <Letter>` |
| Company | `EC7H Synthetic Company` |
| Sales invoice | `EC7H-SINV-0001` style with `EC7H-` prefix |
| Purchase invoice | `EC7H-PINV-0001` style with `EC7H-` prefix |
| Scenario mapping key | Existing `V1RA-###` IDs only |

Forbidden naming patterns:

- real bank names,
- real company names,
- real customer names,
- real supplier names,
- real person names,
- production-looking bare document IDs such as `SINV-0001`, `SO-0001`, `PO-0001`,
- arbitrary IDs not linked to the manifest,
- unknown scenario IDs.

## Validation Rules

Future validation must enforce:

| Rule | Expected behavior |
| --- | --- |
| Manifest name must match `V1_BROWSER_UAT_SYNTHETIC_SET_001` | Reject otherwise |
| Site must be non-production | Reject production/unknown site |
| Synthetic marker must not override raw identifier detection | Reject real-like identifiers even if labeled synthetic |
| Bare production-style document IDs are forbidden | Reject `SINV-0001`, `SO-0001`, `PO-0001`, and similar |
| Synthetic document IDs must be clearly prefixed | Accept only approved IDs such as `EC7H-SINV-0001` |
| Scenario IDs must be known | Reject unknown/unmapped scenario identifiers |
| Smoke-10 mappings must be complete before execution | Missing mappings become `uat_blocked_dataset` |
| No real names | Reject real bank/company/customer/supplier/person-like names |
| No secrets | Reject passwords, tokens, session IDs, cookies, site configs |
| No raw trace fields | Reject trace payloads in dataset manifest |

## Example Template Shape

This is illustrative only. It is not an approved `.json` file and must not be treated as executable data.

```text
manifest_name: V1_BROWSER_UAT_SYNTHETIC_SET_001
site_label: TBD_NON_PRODUCTION_SITE_LABEL
company: EC7H Synthetic Company
date_context: TBD_SYNTHETIC_DATE_CONTEXT
customers:
  - id: EC7H-CUST-A
    name: EC7H Synthetic Customer A
  - id: EC7H-CUST-B
    name: EC7H Synthetic Customer B
suppliers:
  - id: EC7H-SUP-A
    name: EC7H Synthetic Supplier A
items:
  - id: EC7H-ITEM-A
    name: EC7H Synthetic Item A
sales_invoices:
  - id: EC7H-SINV-0001
    customer_id: EC7H-CUST-A
scenario_mappings:
  V1RA-001:
    records: [EC7H-CUST-A, EC7H-CUST-B]
  V1RA-033:
    records: [EC7H-SINV-0001, EC7H-CUST-A]
```

## Artifact Boundary

V1-R-F does not create:

- `.json` manifest files,
- seed/data files,
- ERP records,
- screenshots,
- traces,
- browser logs,
- source files,
- test files.

Future manifest creation must be separately approved and must avoid:

- ERP UI paths,
- seed/data paths unless explicitly approved for synthetic data setup,
- temp/probe/cache paths,
- PrimeAxis paths,
- generated scratch paths,
- raw trace/redacted trace JSON paths,
- site config paths,
- secret/archive-content paths.

## Current Safety Assessment

The manifest template is safe for Counterpart/QA review because it is documentation-only and uses clearly synthetic placeholder names. It does not create executable data or ERP records.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS |
| Durable helper presence | PASS: `/tmp/ec8b_verify.py` exists |
| Fake-Frappe `service.py` import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Actual `.json` manifest file | Not created |
| Seed/data files | Not created |
| ERP writes | Not performed |
| Browser execution | Not run |
| Screenshots/traces | Not captured |
| Source/test edits | None |
| Staging | Not performed |

## V1-R-F Decision

`v1_r_f_synthetic_dataset_manifest_template_ready_for_counterpart_qa_review`
