# Qwen ERP Governed Scope Coverage Round 1 Phase 1 Front-Door Inventory

Status: active research note
Date: 2026-04-12
Scope: Round 1 Phase 1 inventory for `customer`, `supplier`, and `item/product` across front-door and metadata activation seams

## 1. Purpose

This note records the first inventory pass for Round 1.

Round 1 scope:

1. customer
2. supplier
3. item or produc

This phase is inventory only.

It answers:

1. what is declared at the front door and metadata layer
2. what is activated for fresh business routing
3. where support exists only in adjacent families
4. where the seams are uneven across the three grains

This note does not claim runtime closure.
Runtime consumption and behavior truthing belong to later phases.

## 2. Evidence Sources

The inventory was based on direct inspection of these active metadata files:

1. `impl_factory/03_config/qwen_enterprise_metadata/frontdoor_intent_registry.json`
2. `impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json`
3. `impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json`
4. `impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json`
5. `impl_factory/03_config/qwen_enterprise_metadata/report_registry.json`
6. `impl_factory/03_config/qwen_enterprise_metadata/entity_reference_policy_registry.json`
7. `impl_factory/03_config/qwen_enterprise_metadata/composite_family_registry.json`
8. `impl_factory/03_config/qwen_enterprise_metadata/composite_artifact_registry.json`

## 3. Front-Door Finding

The front door is intentionally grain-agnostic.

`frontdoor_intent_registry.json` currently contains only high-level front-door classes such as:

1. `greeting`
2. `thanks`
3. `acknowledgement`
4. `capability_question`
5. `governed_kpi_definition`
6. `governed_kpi_value`
7. `governed_composite_value`
8. `session_flow`
9. `low_signal_non_business`
10. `closure_signoff`
11. `route_onward`

Important conclusion:

1. grain-specific business support is not declared in the front-door registry itself
2. business-grain activation begins in the semantic-resolution and capability layers
3. therefore Phase 1 inventory must treat front-door support as:
   - generic route ownership at the front door
   - specific grain ownership in downstream registries

This is not a defect by itself.
It is the current architecture shape.

## 4. Semantic Registry Findings

### 4.1 Shared Semantic Vocabulary Exists

`semantic_resolution_registry.json` already defines the following shared slots:

1. `entity_grain`
   - allowed values include `customer`, `supplier`, `item`, `warehouse`
2. `lookup_mode`
   - `directory_list`
   - `candidate_resolution`
   - `profile_target`
3. `lookup_projection`
   - `names_only`
   - `standard_directory`
   - `selected_columns`

Important conclusion:

1. the semantic layer already knows how to express lookup-style requests
2. the missing issue is not absence of semantic vocabulary
3. the missing issue is uneven activation below that vocabulary

### 4.2 Grain Alias Coverage Exists

Alias coverage is already declared for:

1. `customer`
2. `supplier`
3. `item`

Important declared alias pattern:

1. `item` aliases include `product`, `products`, `product name`, and `product names`

This is useful because it means the semantic layer already treats product wording as an `item` grain in at least one core slot.

### 4.3 Lookup Semantic Slots Are Shared Across Grains

The semantic layer already includes:

1. directory-style language
2. candidate-resolution language
3. profile-target language

Examples from declared lookup-mode aliases:

1. `give me some`
2. `names`
3. `similar to`
4. `called`
5. `details about`
6. `tell me more about`

Important conclusion:

1. Phase 1 evidence does not support a claim that the system lacks semantic understanding for these asks
2. the stronger evidence is that activation below the semantic layer is uneven

### 4.4 Family Resolution Is Not Symmetrical

Only one direct `master_data_lookup` family-resolution rule exists for Round 1 grains:

1. `master_customer_directory`

No equivalent rules were found for:

1. `master_supplier_directory`
2. `master_item_directory`

Important conclusion:

1. customer is activated for direct master-data lookup
2. supplier and item are not activated in the same family
3. this is the first major metadata asymmetry in Round 1

## 5. Capability Registry Findings

### 5.1 Customer Master Lookup Is Explicitly Activated

The capability registry contains:

1. `customer_master_read`

That capability is explicitly tied to:

1. intent class `master_data_lookup`
2. report family `customer_master_list`
3. report `Customer Master List`

### 5.2 Supplier And Item/Product Exist Elsewhere, But Not In The Same Lookup Seam

The capability registry also contains strong non-master-data capabilities such as:

1. `accounts_payable_read`
2. `accounts_receivable_read`
3. `product_performance_read`
4. `stock_read`
5. `sales_read`
6. `purchase_order_read`

These prove that supplier and item/product are not absent from the governed system.

But they do not prove that supplier and item/product are activated for direct master-data lookup.

No direct capability entries were found for:

1. `supplier_master_read`
2. `item_master_read`
3. `product_master_read`

Important conclusion:

1. supplier and item/product already exist in governed analytics and document families
2. they are not yet symmetrically activated in the direct lookup family

## 6. Report Family And Report Findings

### 6.1 Customer Has A Real Master Family

The report family registry contains:

1. `customer_master_list`

The report registry contains:

1. `Customer Master List`

That report is direct-query backed and already defines:

1. doctype `Customer`
2. supported lookup fields
3. filterable fields
4. default limi
5. approved follow-up modes

This is a full master-data route, not just a semantic hint.

### 6.2 Supplier Has No Equivalent Master Family In Current Metadata

No active equivalents were found for:

1. `supplier_master_list`
2. `Supplier Master List`

Supplier does appear in other governed surfaces such as:

1. `Accounts Payable Summary`
2. `Purchase Order List`

But those are different families with different purposes.

### 6.3 Item/Product Has No Equivalent Master Family In Current Metadata

No active equivalents were found for:

1. `item_master_list`
2. `product_master_list`
3. `Item Master List`
4. `Product Master List`

Item/product does appear in other governed surfaces such as:

1. `Sales Analytics`
2. `Gross Profit`
3. `Item-wise Sales History`
4. `Stock Balance`

Again, those are adjacent governed families, not direct master-data lookup activation.

## 7. Entity Reference Policy Findings

The entity reference policy registry currently contains only one Round 1 grain policy:

1. `customer`

That policy declares:

1. doctype `Customer`
2. identity and display fields
3. search fields
4. allowed lookup modes:
   - `directory_list`
   - `candidate_resolution`
   - `profile_target`
5. default projection
6. default limi
7. match policy

No equivalent entity reference policies were found for:

1. `supplier`
2. `item`

Important conclusion:

1. customer candidate resolution is metadata-backed
2. supplier and item candidate resolution are not yet activated by the same registry seam

## 8. Composite And Adjacent Family Findings

The system already has active adjacent governed support beyond master-data lookup.

Examples:

1. `customer_commercial_ranking` composite family is active
2. `product_commercial_ranking` composite family is active
3. `accounts_receivable_read` gives customer-based aging and outstanding surfaces
4. `accounts_payable_read` gives supplier-based aging and outstanding surfaces
5. `product_performance_read` and `stock_read` give item/product governed surfaces

Important conclusion:

1. Round 1 grains are already present in the system
2. but presence is fragmented across families
3. direct lookup/navigation activation is much stronger for customer than for supplier and item/produc

## 9. Naming And Taxonomy Unevenness

A real metadata unevenness exists between `item` and `product`.

Examples:

1. `entity_grain` uses `item`
2. `inventory_axis` uses `item`
3. `ranking_subject` uses `product`
4. product-performance families describe the same business surface with product language

This does not yet prove a runtime bug.

But it is a Phase 1 classification finding because:

1. it increases translation burden across seams
2. it may hide support asymmetry
3. it should be checked carefully in Phase 2 and Phase 3

## 10. Round 1 Phase 1 Classification Matrix

| Grain | Semantic grain declared | Direct `master_data_lookup` rule | Direct lookup capability | Direct lookup family/report | Entity reference policy | Adjacent governed families present | Phase 1 classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Customer | Yes | Yes | Yes | Yes | Yes | Yes | Strongly activated in direct lookup and adjacent families |
| Supplier | Yes | No | No | No | No | Yes | Present in adjacent governed families, not activated in direct lookup seam |
| Item/Product | Yes | No | No | No | No | Yes | Present in adjacent governed families, not activated in direct lookup seam; terminology uneven between `item` and `product` |

## 11. Phase 1 Conclusions

Round 1 Phase 1 establishes these facts:

1. the semantic layer already supports customer, supplier, and item/product vocabulary
2. the front door is intentionally generic and routes business meaning onward
3. customer has a true direct lookup seam in metadata
4. supplier does not have a symmetric direct lookup seam in current metadata
5. item/product does not have a symmetric direct lookup seam in current metadata
6. supplier and item/product are already governed in other families, so the issue is not total absence from the system
7. item/product naming is uneven across metadata seams and should be examined carefully in runtime mapping

## 12. What This Phase Does Not Yet Claim

This note does not yet claim:

1. which metadata entries are actually consumed end to end
2. where runtime still branches directly by grain
3. whether the active metadata behaves correctly in fresh query, follow-up, and detail handoff
4. whether supplier/item lookup can be enabled safely by activation only, or needs new governed source wiring

Those belong to Round 1 Phase 2 and Phase 3.

## 13. Next Step

Next step:

1. Round 1, Phase 2
2. inspect runtime consumption for:
   - front-door to semantic handoff
   - fresh query interpretation
   - family resolution
   - entity reference resolution
   - entity detail handoff
   - follow-up continuity

Phase 2 should answer:

1. where metadata is already consumed correctly
2. where customer currently has special runtime treatmen
3. where supplier and item/product lack runtime consumption versus merely lacking metadata activation
