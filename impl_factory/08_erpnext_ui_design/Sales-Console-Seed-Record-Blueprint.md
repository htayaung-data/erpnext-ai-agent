# Sales Console Seed Record Blueprint

Status: exact record blueprint for seeded `Sales Console` scenario coverage  
Scope: define the concrete alias-level transaction package to create before import execution  
Source authority: [Sales-Console-Seed-Batch-Plan.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Batch-Plan.md), [Sales-Console-Seed-Execution-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Execution-Spec.md)

## 1. Purpose

This document defines the exact records to create as part of the `Sales Console` scenario seed package.

These are blueprint aliases, not final ERP document names.

Use them so every record has:

1. a business purpose
2. a scenario code
3. a known link chain
4. a validation target inside the console

## 2. Customer Portfolio

| Customer Alias | Territory | Main Use |
|---|---|---|
| `Maha Bandula Mobile Wholesale` | Yangon | manager quotation and order approval |
| `Theingyi Telecom Distribution` | Yangon | executive quotation and order approval |
| `Hledan Mobile Trade Center` | Yangon | open order and partial delivery |
| `Zegyo Mobile Supply House` | Mandalay | due-soon and partial delivery |
| `Lanmadaw Digital Wholesale` | Yangon | overdue, partly paid, paid invoices |
| `Pazundaung Mobile Distribution` | Yangon | overdue, partly paid, paid invoices |
| `Thaketa Mobile Exchange` | Yangon | return invoice and delivery return |
| `Chan Aye Mobile Trading Hub` | Mandalay | mixed-history inquiry |

## 3. Quotations

| Alias | Customer | Scenario | Target State | Practical Intent |
|---|---|---|---|---|
| `Q-APPR-01` | `Maha Bandula Mobile Wholesale` | `SC-01` | `Pending Sales Approval` | manager approval due to moderate exception |
| `Q-APPR-02` | `Maha Bandula Mobile Wholesale` | `SC-01` | `Pending Sales Approval` | manager approval due to discount |
| `Q-APPR-03` | `Theingyi Telecom Distribution` | `SC-01` | `Pending Sales Approval` | manager approval due to value band |
| `Q-EXEC-01` | `Theingyi Telecom Distribution` | `SC-02` | `Pending Executive Approval` | executive approval due to high value |
| `Q-EXEC-02` | `Theingyi Telecom Distribution` | `SC-02` | `Pending Executive Approval` | executive approval due to deep discount |
| `Q-ACT-01` | `Chan Aye Mobile Trading Hub` | support | `Draft` or open actionable state | quotation requiring revision |
| `Q-ACT-02` | `Hledan Mobile Trade Center` | support | `Draft` or open actionable state | routine quotation follow-up |
| `Q-ACT-03` | `Zegyo Mobile Supply House` | support | `Draft` or open actionable state | near-expiry quotation |

## 4. Sales Orders

| Alias | Customer | Scenario | Target State | Delivery Shape |
|---|---|---|---|---|
| `SO-BLK-01` | `Maha Bandula Mobile Wholesale` | `SC-11` | `Pending Sales Approval` | not yet delivered |
| `SO-BLK-02` | `Theingyi Telecom Distribution` | `SC-11` | `Pending Sales Approval` | not yet delivered |
| `SO-BLK-03` | `Theingyi Telecom Distribution` | `SC-11` | `Pending Executive Approval` | not yet delivered |
| `SO-FUL-01` | `Hledan Mobile Trade Center` | `SC-03` | `Approved` | pending fulfillment |
| `SO-FUL-02` | `Hledan Mobile Trade Center` | `SC-03` | `Approved` | pending fulfillment and due soon |
| `SO-FUL-03` | `Zegyo Mobile Supply House` | `SC-03` | `Approved` | pending fulfillment and due soon |
| `SO-PDL-01` | `Hledan Mobile Trade Center` | `SC-05` | `Approved` | partially delivered |
| `SO-PDL-02` | `Zegyo Mobile Supply House` | `SC-05` | `Approved` | partially delivered |
| `SO-DUE-01` | `Zegyo Mobile Supply House` | `SC-04` | `Approved` | due soon, no delivery yet |
| `SO-MIX-01` | `Chan Aye Mobile Trading Hub` | `SC-12` | `Approved` | routine open order |

## 5. Delivery Notes

| Alias | Customer | Linked Order | Scenario | Target Shape |
|---|---|---|---|---|
| `DN-PDL-01A` | `Hledan Mobile Trade Center` | `SO-PDL-01` | `SC-05` | first partial delivery |
| `DN-PDL-01B` | `Hledan Mobile Trade Center` | `SO-PDL-01` | `SC-05` | second partial or remaining delivery slice |
| `DN-PDL-02A` | `Zegyo Mobile Supply House` | `SO-PDL-02` | `SC-05` | first partial delivery |
| `DN-FUL-01` | `Chan Aye Mobile Trading Hub` | `SO-MIX-01` | `SC-12` | normal delivery |
| `DN-RET-01` | `Thaketa Mobile Exchange` | original chain | `SC-10` | delivery return against original delivery |

## 6. Sales Invoices

| Alias | Customer | Scenario | Target Status | Upstream Shape |
|---|---|---|---|---|
| `INV-OVD-01` | `Lanmadaw Digital Wholesale` | `SC-06` | `Overdue` | may be direct invoice |
| `INV-OVD-02` | `Lanmadaw Digital Wholesale` | `SC-06` | `Overdue` | linked to order if useful |
| `INV-OVD-03` | `Pazundaung Mobile Distribution` | `SC-06` | `Overdue` | linked to order if useful |
| `INV-OVD-04` | `Pazundaung Mobile Distribution` | `SC-06` | `Overdue` | may be direct invoice |
| `INV-PPD-01` | `Lanmadaw Digital Wholesale` | `SC-08` | `Partly Paid` | invoice with partial payment |
| `INV-PPD-02` | `Pazundaung Mobile Distribution` | `SC-08` | `Partly Paid` | invoice with partial payment |
| `INV-PAI-01` | `Lanmadaw Digital Wholesale` | `SC-07` | `Paid` | linked payment entry |
| `INV-PAI-02` | `Pazundaung Mobile Distribution` | `SC-07` | `Paid` | linked payment entry |
| `INV-PAI-03` | `Pazundaung Mobile Distribution` | `SC-07` | `Paid` | linked payment entry |
| `INV-RET-01` | `Thaketa Mobile Exchange` | `SC-09` | `Return` | return against original invoice |
| `INV-MIX-01` | `Chan Aye Mobile Trading Hub` | `SC-12` | `Paid` or `Overdue` | mixed customer-history record |

## 7. Payment Entries

| Alias | Customer | Scenario | Linked Invoice | Payment Shape |
|---|---|---|---|---|
| `PAY-PAI-01` | `Lanmadaw Digital Wholesale` | `SC-07` | `INV-PAI-01` | full receipt |
| `PAY-PAI-02` | `Pazundaung Mobile Distribution` | `SC-07` | `INV-PAI-02` | full receipt |
| `PAY-PAI-03` | `Pazundaung Mobile Distribution` | `SC-07` | `INV-PAI-03` | full receipt |
| `PAY-PPD-01A` | `Lanmadaw Digital Wholesale` | `SC-08` | `INV-PPD-01` | partial receipt |
| `PAY-PPD-02A` | `Pazundaung Mobile Distribution` | `SC-08` | `INV-PPD-02` | partial receipt |
| `PAY-MIX-01` | `Chan Aye Mobile Trading Hub` | `SC-12` | `INV-MIX-01` or other mixed invoice | settlement example |
| `PAY-RET-01` | `Thaketa Mobile Exchange` | support | `INV-RET-01` only if a credit/refund case is needed | optional |
| `PAY-RET-02` | `Thaketa Mobile Exchange` | support | second return-related settlement only if needed | optional |

Practical note:

1. the last 2 payment aliases are optional reserve cases
2. keep total live payment-entry increment near the agreed 8-record ceiling

## 8. Return Chain

| Alias | Customer | Scenario | Return Against | Intent |
|---|---|---|---|---|
| `INV-RET-01` | `Thaketa Mobile Exchange` | `SC-09` | original sales invoice | customer return invoice |
| `INV-RET-02` | `Thaketa Mobile Exchange` | `SC-09` | original sales invoice | second return case if needed |
| `DN-RET-01` | `Thaketa Mobile Exchange` | `SC-10` | original delivery note | delivery return anchor |

## 9. Follow-Up Tasks

| Alias | Allocated To | Reference | Scenario | Description Shape |
|---|---|---|---|---|
| `TD-QUO-01` | `Sales User` | `Q-ACT-01` | `SC-13` | revise quotation after customer feedback |
| `TD-QUO-02` | `Sales User` | `Q-ACT-03` | `SC-13` | follow up before quotation expiry |
| `TD-INV-01` | `Sales User` | `INV-OVD-01` | `SC-13` | call customer on overdue invoice |
| `TD-INV-02` | `Sales Manager` | `INV-OVD-03` | `SC-13` | escalate overdue invoice review |
| `TD-DEL-01` | `Sales User` | `SO-DUE-01` | `SC-13` | confirm delivery commitment |
| `TD-RET-01` | `Sales Manager` | `INV-RET-01` or `DN-RET-01` | `SC-13` | callback on return settlement |

## 10. Item Mix Guidance

Use the live seed item pool across the package with practical variation:

### Higher-value approval and executive cases

1. `SPH-APP-IP14-128`
2. `SPH-XMI-RN13-8/256`
3. `SPH-SAM-A15-6/128`

### Routine fulfillment and billing cases

1. `SPH-OPP-A58-6/128`
2. `ACC-CHR-XMI-33W`
3. `ACC-PWB-BAS-20K`
4. `MEM-MSD-SND-128`
5. `ACC-SP-GLS-RN13`

## 11. Practical Design Rules

When building the actual import rows:

1. do not make every order multi-item; mix simple and slightly richer documents
2. do not make every approval case discount-driven; use both value and discount triggers
3. keep at least 2 direct-invoice style records so inquiry can prove partial-chain behavior
4. keep at least 1 fully linked order -> delivery -> invoice -> payment chain
5. keep at least 1 return anchored by invoice and 1 return anchored by delivery

## 12. Review Use

This blueprint is the review checkpoint before actual loading.

If this alias package is accepted, the next implementation layer should convert it into:

1. actual import rows
2. actual ERP document creation order
3. controlled batch execution
