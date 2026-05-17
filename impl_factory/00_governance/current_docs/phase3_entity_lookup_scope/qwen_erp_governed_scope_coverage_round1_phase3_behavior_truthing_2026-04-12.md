# Qwen ERP Governed Scope Coverage Round 1 Phase 3 Behavior Truthing

Status: active research note
Date: 2026-04-12
Scope: Round 1 Phase 3 behavior truthing for `customer`, `supplier`, and `item/product`

## 1. Purpose

This note compares the Round 1 Phase 1 and Phase 2 analysis against actual bounded behavior.

Round 1 scope:

1. customer
2. supplier
3. item or produc

This phase is not broad manual replay.

It uses:

1. targeted contract tests
2. controlled inline runtime checks
3. bounded metadata/runtime confirmation

The goal is to classify:

1. confirmed behaviors
2. contradicted assumptions
3. unresolved behaviors that need Phase 4 gap classification

## 2. Evidence Sources

Phase 3 truthing used these checks:

1. `python3 -m unittest ai_assistant_ui.tests.test_customer_master_lookup_contracts ai_assistant_ui.tests.test_followup_interpreter_contracts`
2. `python3 -m unittest ai_assistant_ui.tests.test_entity_detail_contracts`
3. controlled inline checks for:
   - `_deterministic_family_surface_interpretation(...)`
   - `assess_context_isolation(...)`
4. direct metadata/runtime confirmation for active policies, families, and capabilities

## 3. Test Results

### 3.1 Customer Master Lookup And Follow-Up Tests

Result:

1. `test_customer_master_lookup_contracts`
2. `test_followup_interpreter_contracts`

Status:

1. passed

Observed result:

1. 9 tests ran
2. all passed

### 3.2 Entity Detail Tests

Result:

1. `test_entity_detail_contracts`

Status:

1. passed

Observed result:

1. 43 tests ran
2. all passed

Important conclusion:

1. the customer-focused proof slice is not theoretical
2. it is directly protected by bounded contract tests

## 4. Controlled Runtime Truthing

### 4.1 Deterministic Customer Directory Works As Expected

Check:

1. `give me some customer names`

Observed deterministic result:

1. intent class = `master_data_lookup`
2. capability = `customer_master_read`
3. report = `Customer Master List`
4. slots include:
   - `entity_grain = customer`
   - `lookup_mode = directory_list`
   - `lookup_projection = names_only`

Truth status:

1. confirmed

This matches both Phase 1 metadata inventory and Phase 2 runtime seam mapping.

### 4.2 Deterministic Customer Candidate Resolution Works At Interpretation Level

Check:

1. `do u have customer name similar to Nay Lin Mobile`

Observed deterministic result:

1. intent class = `master_data_lookup`
2. capability = `customer_master_read`
3. report = `Customer Master List`
4. slots include:
   - `entity_grain = customer`
   - `lookup_mode = candidate_resolution`
   - `lookup_projection = names_only`
   - `lookup_search_text = Nay Lin Mobile`
   - embedded `entity_reference_resolution`

Important nuance:

1. in the controlled stubbed check, resolution status was `not_found`
2. this is expected under the stubbed no-data environmen
3. the important truth in this phase is that the correct governed path is selected

Truth status:

1. confirmed

### 4.3 Supplier Directory Does Not Enter The Same Deterministic Lookup Lane

Check:

1. `give me some supplier names`

Observed deterministic result:

1. no deterministic family-surface interpretation was produced
2. result = `NONE`

Truth status:

1. confirmed

This matches the Phase 1 finding:

1. supplier has semantic vocabulary
2. but no direct `master_data_lookup` family rule, capability, family, report, or reference policy

### 4.4 Supplier Candidate Resolution Does Not Enter The Same Deterministic Lookup Lane

Check:

1. `do u have supplier name similar to Myanmar Tech`

Observed deterministic result:

1. no deterministic family-surface interpretation was produced
2. result = `NONE`

Truth status:

1. confirmed

This supports the same conclusion:

1. supplier breakout may be understood as navigation inten
2. but there is no symmetric direct lookup execution lane today

### 4.5 Product Names Do Not Route To A Direct Master-Data Lookup Lane

Check:

1. `give me some product names`

Observed deterministic result:

1. intent class = `inventory_summary`
2. capability = `stock_read`
3. report = `Stock Balance`
4. slots include:
   - `inventory_axis = item`

Truth status:

1. confirmed

This is an important behavior truth.

It means:

1. product wording is currently captured by an inventory seam
2. not by a direct master-data lookup seam

This confirms the earlier analysis that:

1. item/product support exists
2. but it exists in adjacent families rather than in a true master-data navigation family

### 4.6 Explicit Profile Request Does Not Deterministically Start At The Fresh Family Surface

Check:

1. `tell me more about Ko Nay Lin Mobile Center`

Observed deterministic result:

1. no deterministic family-surface interpretation was produced
2. result = `NONE`

Truth status:

1. confirmed

Important interpretation:

1. explicit profile requests are not proven through the deterministic fresh family-surface fallback
2. they are handled through the separate entity-detail drilldown path

This does not mean profile requests are unsupported.
It means they are owned by a different runtime lane.

## 5. Follow-Up Breakout Truthing

### 5.1 Supplier Directory Breaks Out Of Customer Detail Contex

Check:

1. `give me some supplier names`
2. grounded context = customer detail artifac

Observed result:

1. `force_new_query = True`
2. `out_of_scope = False`
3. reason states that it is a self-contained governed entity-navigation query

Truth status:

1. confirmed

This proves:

1. the system does not merely stay trapped in stale customer detail contex
2. breakout works at the boundary decision level

### 5.2 Product Names Also Break Out Of Customer Detail Contex

Check:

1. `give me some product names`
2. grounded context = customer detail artifac

Observed result:

1. `force_new_query = True`
2. `out_of_scope = False`

Truth status:

1. confirmed

This is important because it separates:

1. context breakout correctness
2. downstream execution-lane completeness

### 5.3 Customer Similarity Lookup Breaks Out Correctly

Check:

1. `do u have customer name similar to Nay Lin Mobile`
2. grounded context = customer detail artifac

Observed result:

1. `force_new_query = True`
2. `out_of_scope = False`

Truth status:

1. confirmed

### 5.4 Deictic Customer Follow-Up Properly Stays Grounded

Check:

1. `what is this customer's tenure?`
2. grounded context = customer detail artifac

Observed result:

1. `force_new_query = False`
2. `out_of_scope = False`

Truth status:

1. confirmed

Important conclusion:

1. the system already distinguishes deictic continuation from self-contained breakou
2. this is a real working enterprise behavior, not just design inten

## 6. Confirmed vs Contradicted vs Unresolved

### 6.1 Confirmed

The following Phase 1 and Phase 2 conclusions are confirmed by behavior truthing:

1. customer has a real direct master-data lookup lane
2. customer candidate-resolution uses the direct lookup lane
3. supplier does not have a symmetric direct lookup lane
4. breakout from stale entity detail context works for supplier navigation asks
5. breakout from stale entity detail context works for product navigation asks
6. deictic customer detail follow-up remains grounded

### 6.2 Contradicted

No major Phase 1 or Phase 2 conclusion was directly contradicted.

The analysis held up well.

### 6.3 Newly Clarified

Behavior truthing added one important clarification:

1. `give me some product names` currently routes to `inventory_summary` via `Stock Balance`
2. it does not attempt a direct master-data navigation lane

This is not a contradiction.
It is a sharper behavior fact than earlier phases could prove.

### 6.4 Unresolved

The following behaviors remain unresolved at Phase 3:

1. whether supplier could be activated safely by metadata alone, or needs new governed source/family work
2. whether item/product should gain a true direct master-data lane, or continue through adjacent governed families for some asks
3. whether the direct grain branching in `entity_detail.py` can be removed by adaptation of existing shared contracts alone
4. whether a future generalized master-data family should be one shared family shape or several grain-specific family activations under a shared contract pattern

## 7. Round 1 Phase 3 Behavior Matrix

| Ask shape | Observed behavior | Truth reading |
| --- | --- | --- |
| `give me some customer names` | Direct `master_data_lookup` to `Customer Master List` | Customer direct lookup lane is real |
| `do u have customer name similar to Nay Lin Mobile` | Direct `master_data_lookup` candidate-resolution path | Customer resolution lane is real |
| `give me some supplier names` | No deterministic direct lookup interpretation | Supplier direct lookup lane is absent today |
| `do u have supplier name similar to Myanmar Tech` | No deterministic direct lookup interpretation | Supplier resolution lane is absent today |
| `give me some product names` | `inventory_summary` via `Stock Balance` | Product wording currently routes through adjacent governed inventory lane |
| `tell me more about Ko Nay Lin Mobile Center` | Not handled by deterministic family-surface fallback | Profile ask belongs to entity-detail lane, not family-surface fallback |
| `give me some supplier names` after customer detail | Breaks out to new query | Breakout layer is working |
| `give me some product names` after customer detail | Breaks out to new query | Breakout layer is working |
| `what is this customer's tenure?` after customer detail | Stays grounded | Deictic detail continuity is working |

## 8. Phase 3 Conclusion

Round 1 Phase 3 shows that the earlier analysis was directionally correct.

The system truth is:

1. customer direct navigation is genuinely active
2. supplier direct navigation is no
3. product/item language is currently absorbed into adjacent governed families rather than a dedicated master-data lookup lane
4. context breakout is not the main current blocker
5. the bigger current blocker is downstream governed activation and lane completeness

## 9. Next Step

Next step:

1. Round 1, Phase 4
2. classify the gaps by type and priority

Phase 4 should separate:

1. missing metadata activation
2. missing shared runtime consumption
3. customer-weighted downstream adaptation/rendering deb
4. naming and taxonomy unevenness
5. behaviors that should remain deferred until later governed scope expansion
