# Qwen ERP Governed Scope Coverage Round 2 Phase 1 Front-Door Inventory

Status: active research note
Date: 2026-04-13
Scope: Round 2 Phase 1 front-door and metadata inventory for the next governed ERP scope groups beyond Round 1

## 1. Purpose

Round 1 Phase 1 focused on the sample entity-navigation group:

1. customer
2. supplier
3. item / produc

Round 2 Phase 1 now widens the inventory to the next practical governed scope groups:

1. sales document navigation
2. purchase document navigation
3. finance operation surfaces
4. inventory operation surfaces

The goal is not to prove runtime behavior yet.

The goal is to answer, at metadata level:

1. what the front door can already classify generically
2. which of these scope groups already have semantic family-resolution rules
3. which already have capability and report suppor
4. which are only partially activated
5. which are absent and therefore should not be claimed ye

## 2. Evidence Basis

This note is based on direct inspection of:

1. [frontdoor_intent_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/frontdoor_intent_registry.json)
2. [semantic_resolution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json)
3. [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
4. [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json)
5. [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
6. [entity_reference_policy_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/entity_reference_policy_registry.json)
7. [composite_artifact_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_artifact_registry.json)
8. [composite_assembly_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_assembly_registry.json)
9. [composite_compatibility_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_compatibility_registry.json)

## 3. Scope Groups Examined

This note examined these grouped surfaces.

### 3.1 Sales Documents

1. sales invoice
2. sales order
3. delivery note

### 3.2 Purchase Documents

1. purchase order
2. purchase invoice
3. purchase receip

### 3.3 Finance Operations

1. payment entry
2. journal entry
3. accounts receivable
4. accounts payable

### 3.4 Inventory Operations

1. stock balance
2. warehouse inventory
3. inventory item view

## 4. Front-Door Finding

The front-door registry is still broad by design.

It contains generic intent classes such as:

1. greeting
2. thanks
3. acknowledgemen
4. capability question
5. KPI definition
6. KPI execution
7. composite execution
8. continuation
9. governed ERP reques

Important finding:

The front door does not declare document- or operation-specific intent classes for the Round 2 scopes.

That is not automatically a problem.

It means these scopes depend on the deeper semantic resolution layer rather than on highly specific front-door labels.

So the correct reading is:

1. the front door is generic
2. Round 2 scope specificity appears mainly in semantic family rules, capabilities, and reports

## 5. Metadata Inventory Findings

## 5.1 Sales Document Navigation Is Broadly Presen

Sales document surfaces are strongly represented in metadata.

Observed semantic family rules:

1. `transaction_listing_sales_invoice`
2. `transaction_listing_delivery_note`
3. `transaction_listing_sales_order`
4. `trend_sales_amount_fulfillment`
5. `trend_quantity_fulfillment`

Observed capabilities:

1. `sales_read`
2. `sales_order_read`
3. `fulfillment_read`

Observed reports:

1. `Sales Analytics`
2. `Sales Invoice List`
3. `Delivery Note List`
4. `Sales Order List`
5. `Sales Order Item List`
6. `Sales Invoice Item List`
7. `Delivery Note Trends`

Interpretation:

1. sales invoice, sales order, and delivery note already have clear metadata presence
2. sales document coverage is not only analytical; it also includes document listing surfaces
3. delivery note currently appears under fulfillment-oriented metadata rather than a dedicated delivery-specific capability family

## 5.2 Purchase Document Coverage Is Uneven

Observed semantic family rule:

1. `transaction_listing_purchase_order`

Observed capability:

1. `purchase_order_read`

Observed report:

1. `Purchase Order List`

Observed absences in the inspected registries:

1. no semantic rule for purchase invoice
2. no semantic rule for purchase receip
3. no capability for purchase invoice
4. no capability for purchase receip
5. no report entry for purchase invoice
6. no report entry for purchase receip

Interpretation:

1. purchase order has a real declared metadata path
2. purchase invoice and purchase receipt do not currently appear as declared governed paths in this inspected metadata surface
3. they should therefore be treated as absent in this current metadata inventory, not estimated as supported just because ERP data may exist somewhere else

## 5.3 Finance Operations Are Present But Mixed

Observed semantic family rules:

1. `aging_receivable`
2. `aging_payable`
3. `ranking_customer_outstanding_total`
4. `ranking_supplier_outstanding_total`

Observed capabilities:

1. `collections_read`
2. `accounts_receivable_read`
3. `accounts_payable_read`

Observed reports:

1. `Payment Entry List`
2. `Accounts Payable`
3. `Accounts Payable Summary`
4. `Accounts Receivable`
5. `Accounts Receivable Summary`

Important partial activation finding:

1. `Payment Entry List` exists as a repor
2. `collections_read` exists as a capability
3. but no semantic family rule for payment entry was found in the inspected semantic registry

Observed absence:

1. no journal entry semantic rule
2. no journal entry capability
3. no journal entry report entry

Interpretation:

1. AR/AP aging and outstanding ranking are clearly declared
2. payment entry is present at capability/report level but not yet visibly activated through a semantic family rule in this inventory
3. journal entry is absent from the current inspected path

## 5.4 Inventory Operations Are Present, But Mostly Snapshot-Oriented

Observed semantic family rules:

1. `inventory_snapshot_item`
2. `inventory_snapshot_warehouse`

Observed capability:

1. `stock_read`

Observed families:

1. `inventory_snapshot`
2. `ranking_analytics`

Observed reports:

1. `Stock Balance`
2. `Warehouse Wise Stock Balance`
3. `Gross Profit`

Interpretation:

1. inventory coverage is clearly presen
2. the visible declared shape is snapshot-oriented rather than master-navigation-oriented
3. warehouse appears as a supported axis inside inventory surfaces
4. this is different from a direct entity-navigation lane for warehouse master data

## 6. Entity Reference And Composite Surface Findings

## 6.1 Entity Reference Policy Is Still Very Narrow

The inspected entity reference policy registry currently shows one active policy:

1. customer

That policy allows:

1. `directory_list`
2. `candidate_resolution`
3. `profile_target`

Interpretation:

1. direct governed entity-reference policy is still customer-first in the current declared surface
2. Round 2 scopes such as delivery note, payment entry, warehouse, and purchase document entities are not yet shown as active entity-reference policies in this registry
3. this is important because capability/report presence alone does not imply direct named-entity navigation suppor

## 6.2 Composite Registries Are Richer Than Entity Reference Policy

Observed composite presence includes references to:

1. customer
2. item / produc
3. sales order
4. sales invoice

Interpretation:

1. some Round 2-relevant business surfaces already exist in composite metadata
2. but that does not automatically mean direct lookup, profile navigation, or named-entity resolution is active for those same scopes
3. composite richness and navigation richness remain separate concerns

## 7. Round 2 Phase 1 Classification

The next governed scope groups can be classified as follows.

### 7.1 Strongly Present In Metadata

1. sales invoice listing
2. sales order listing
3. delivery note listing
4. purchase order listing
5. AR/AP aging
6. outstanding ranking by customer or supplier
7. inventory snapshot by item or warehouse

### 7.2 Present But Partially Activated

1. payment entry
   Reason:
   report and capability are present, but no semantic family rule was found in this inventory

2. delivery note direct named-entity navigation
   Reason:
   listing/trend coverage exists, but no active entity-reference policy was found for this grain

3. warehouse direct named-entity navigation
   Reason:
   warehouse exists as an inventory axis, not yet as a visible direct navigation policy in this inventory

### 7.3 Absent In The Current Inspected Metadata Surface

1. purchase invoice
2. purchase receip
3. journal entry

These are absent in the specific registries inspected for this phase and should be treated as not currently declared in this governed path until later evidence proves otherwise.

## 8. Main Round 2 Phase 1 Findings

Round 2 Phase 1 reveals three important patterns.

### 8.1 Metadata Breadth Is Wider Than Round 1

The project already has significant declared breadth beyond customer/supplier/item.

This is a positive finding.

### 8.2 Activation Is Still Layered And Uneven

Some surfaces are:

1. present in semantic rules
2. present in capabilities
3. present in reports

Others are only:

1. present in reports and capabilities but not semantic rules
2. present as dimensions/axes but not navigation grains
3. present in composite registries but not in entity-reference policy

This continues the same declared-versus-active distinction seen in Round 1.

### 8.3 Document And Operational Coverage Are Not One Uniform Category

The next scope groups split naturally into:

1. document listing paths
2. aging/ranking analytical paths
3. inventory snapshot paths
4. still-weak direct navigation/reference paths

That means later expansion should not assume one single generic pattern for all Round 2 scopes.

## 9. Implication For Round 2 Phase 2

The next step should be runtime seam mapping for the Round 2 groups that now show meaningful metadata presence.

That means Phase 2 should focus on how the runtime consumes these declared paths for:

1. sales invoice
2. sales order
3. delivery note
4. purchase order
5. AR/AP
6. payment entry partial path
7. inventory item/warehouse snapshot paths

Special attention should go to:

1. declared-but-partial activation such as payment entry
2. axis-based scopes such as warehouse
3. the difference between listing support and direct named-entity navigation suppor

## 10. Current Status Statemen

Round 2 Phase 1 is now started and documented.

Current status:

1. the next metadata surface is wider than Round 1
2. strong document, aging, and inventory coverage already exists
3. direct navigation/reference policy remains much narrower than report/capability breadth
4. partial activation remains a central enterprise pattern that Round 2 must continue to map carefully
