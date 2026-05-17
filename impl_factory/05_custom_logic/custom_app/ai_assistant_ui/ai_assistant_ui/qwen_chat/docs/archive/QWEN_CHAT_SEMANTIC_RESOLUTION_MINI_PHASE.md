# Qwen Chat Semantic Resolution Mini Phase

Status: design approved for pre-implementation planning  
Audience: AI/ML, backend, ERP governance maintainers  
Scope: replace tactical phrase-routing with structured semantic resolution  
Non-goal: do not implement runtime behavior changes in this phase

## 1. Why This Mini Phase Exists

The current refactor has improved structure, but the routing architecture must be corrected before more refactoring continues.

We explicitly reject:

1. phrase-specific runtime branches in Python
2. report selection based on hardcoded lexical checks
3. growing one-off routing fixes for individual failing prompts

We accept only one transition path:

1. structured semantic interpretation first
2. governed metadata resolution second
3. bounded lexical aliasing only as slot normalization support

This mini phase exists to define that replacement architecture before any implementation work begins.

## 2. Current State

### 2.1 Cleaned Runtime State

The interrupted tactical keyword-routing patch has been removed from runtime code.

Specifically:

1. no keyword-preference runtime logic remains in `family_tool_surface.py`
2. no keyword-driven capability/report override remains in `fresh_query_interpreter.py`

### 2.2 Current Semantic-Governed Coverage

The semantic-resolution runtime is now active for these governed intents:

1. `financial_statement`
2. `inventory_summary`
3. `aging_analysis`
4. `trend_analysis`
5. `ranked_entities`
6. `product_performance`
7. `transaction_listing`

For these intents:

1. semantic resolution is the authoritative governed routing layer
2. deterministic family-surface fallback is not allowed to re-enter the path
3. legacy runtime must not attach family-surface steering when compiled fallback artifacts already identify one of these intents

### 2.3 Remaining Contract Alignment

One evaluation-registry change currently remains:

1. `product_profitability_last_month`
2. message: `Which products are performing well last month`
3. expected compiler decision changed from `execute` to `clarify`

This should remain only if product/governance agrees that clarification is the correct contract.

If product intent is that the system should execute directly, that registry change must be reverted and solved through the new semantic-resolution path.

### 2.4 Remaining Legacy Intent

After the current migration wave, one intent still remains explicitly legacy-only:

1. `financial_summary`

This is intentional for now.

`financial_summary` is not a narrow single-family intent.
It is a cross-domain summary umbrella that can currently touch:

1. sales
2. inventory
3. receivable
4. payable
5. statement
6. product profitability

That means it must not be migrated by copying the same pattern used for narrower intents.

Its next phase is design-first:

1. semantic decomposition into narrower governed intents when one domain is dominant
2. governed composite execution when the request is truly cross-domain

Reference design artifact:

1. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_semantic_design.json`

## 3. Enterprise Design Goal

The target architecture is:

1. user message enters semantic interpretation
2. semantic interpretation produces structured slots and ambiguity state
3. governed resolver maps structured slots to family/capability/report candidates
4. compiler receives only governed structured candidates
5. clarification is triggered only from structured ambiguity, not from missing keyword hacks

The system must become:

1. auditable
2. deterministic at the governed layer
3. metadata-driven where business policy belongs
4. resistant to incremental keyword sprawl

## 4. Design Rules

### 4.1 Zero-Tolerance Rules

The following are prohibited in runtime routing code:

1. direct phrase-to-report branches
2. direct phrase-to-family branches
3. direct phrase-to-capability overrides
4. special-case fixes for one prompt unless formally modeled in metadata and backed by structured slots

Examples of prohibited runtime logic:

1. if text contains `profit and loss`, force `Profit and Loss Statement`
2. if text contains `warehouse`, force `Warehouse Wise Stock Balance`
3. if text contains `gross profit`, force `Gross Profit`

### 4.2 What Is Allowed

Allowed:

1. lexical normalization for slot extraction
2. metadata-defined alias dictionaries
3. structured slot inference
4. governed metadata resolution rules from slots to reports
5. explicit ambiguity policies in metadata

## 5. New Concept: Semantic Resolution

Semantic resolution is a distinct governed step between:

1. fresh-query semantic interpretation
2. compiler report selection

Its job is to answer:

1. what business shape is the user asking for?
2. which governed slot values are resolved?
3. what ambiguity still remains?
4. which family/capability/report candidates are valid from those structured semantics?

## 6. New Contract

Proposed contract name:

1. `qwen_semantic_resolution_contract`

Proposed responsibilities:

1. carry normalized structured slot resolution
2. record whether the decision came from semantic certainty, metadata default, or bounded fallback
3. expose ambiguity in a governed, inspectable form
4. feed compiler inputs without raw phrase-routing logic

### 6.1 Contract Schema

```json
{
  "type": "qwen_semantic_resolution_contract",
  "contract_version": "1.0",
  "request_id": "string",
  "session_id": "string",
  "intent_class": "string",
  "primary_business_area": "string",
  "resolved_slots": {
    "statement_variant": "string",
    "inventory_axis": "string",
    "ranking_subject": "string",
    "ranking_metric": "string",
    "entity_grain": "string",
    "time_scope": "string",
    "comparison_mode": "string",
    "report_grain": "string"
  },
  "slot_confidence": {
    "statement_variant": 0.0,
    "inventory_axis": 0.0,
    "ranking_subject": 0.0,
    "ranking_metric": 0.0,
    "entity_grain": 0.0,
    "time_scope": 0.0,
    "comparison_mode": 0.0,
    "report_grain": 0.0
  },
  "candidate_family_ids": ["string"],
  "candidate_capability_ids": ["string"],
  "candidate_reports": ["string"],
  "ambiguity_flags": ["string"],
  "ambiguity_reason": "string",
  "resolution_source": {
    "intent_class": "semantic_runtime|metadata_default|governed_fallback",
    "statement_variant": "semantic_runtime|metadata_alias|metadata_default|unresolved",
    "inventory_axis": "semantic_runtime|metadata_alias|metadata_default|unresolved",
    "ranking_subject": "semantic_runtime|metadata_alias|metadata_default|unresolved",
    "ranking_metric": "semantic_runtime|metadata_alias|metadata_default|unresolved",
    "entity_grain": "semantic_runtime|metadata_alias|metadata_default|unresolved",
    "time_scope": "semantic_runtime|metadata_default|unresolved"
  },
  "governed_decision": "execute|clarify|reject",
  "governed_reason": "string",
  "created_at": "ISO-8601 timestamp"
}
```

### 6.2 Initial Slot Set

The first mini phase should support these slots only:

1. `statement_variant`
2. `inventory_axis`
3. `ranking_subject`
4. `ranking_metric`
5. `entity_grain`
6. `time_scope`

Do not expand the slot surface until the first two domains are stable.

`financial_summary` is the exception.

If it is migrated later, it should use a separate second-wave slot set such as:

1. `summary_domains`
2. `summary_focus`
3. `summary_metric_family`
4. `summary_grain`
5. `time_scope`

Those slots should not be added to the active runtime semantic registry until the decomposition-versus-composite strategy is approved.

## 7. New Registry

Proposed file:

1. `impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json`

This registry is not a keyword-routing table.
It is a governed semantic-resolution table.

Its purpose is:

1. define allowed slots
2. define allowed slot values
3. define alias dictionaries for slot normalization
4. define slot-to-family/report resolution rules
5. define ambiguity policies

### 7.1 Registry Top-Level Shape

```json
{
  "contract_version": "1.0",
  "slot_definitions": [],
  "alias_maps": {},
  "family_resolution_rules": [],
  "ambiguity_policies": [],
  "defaults": {}
}
```

`financial_summary` should not be added to this active runtime registry by default.

Until its architecture is approved, its semantic design should remain in a separate non-runtime planning artifact:

1. `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_semantic_design.json`

### 7.2 Slot Definitions

```json
{
  "slot_name": "statement_variant",
  "allowed_values": [
    "profit_and_loss",
    "balance_sheet",
    "cash_flow"
  ],
  "required_for_intent_classes": ["financial_statement"],
  "resolution_mode": "required_or_clarify"
}
```

```json
{
  "slot_name": "inventory_axis",
  "allowed_values": [
    "item",
    "warehouse"
  ],
  "required_for_intent_classes": ["inventory_summary"],
  "resolution_mode": "required_or_default"
}
```

### 7.3 Alias Maps

Alias maps are allowed only for slot normalization, not direct routing.

Example:

```json
{
  "statement_variant": {
    "profit_and_loss": [
      "profit and loss",
      "profit & loss",
      "p&l",
      "p & l",
      "income statement"
    ],
    "balance_sheet": [
      "balance sheet"
    ],
    "cash_flow": [
      "cash flow",
      "cashflow"
    ]
  }
}
```

Example:

```json
{
  "inventory_axis": {
    "warehouse": [
      "by warehouse",
      "warehouse wise",
      "per warehouse"
    ],
    "item": [
      "by item",
      "item wise",
      "per item"
    ]
  }
}
```

These aliases are transitional semantic aids, not final routing logic.

### 7.4 Family Resolution Rules

Rules resolve from structured slots to governed outcomes.

Example:

```json
{
  "rule_id": "financial_statement_profit_and_loss",
  "intent_class": "financial_statement",
  "required_slots": {
    "statement_variant": "profit_and_loss"
  },
  "candidate_family_ids": ["financial_statement"],
  "candidate_capability_ids": ["financial_statement_read"],
  "candidate_reports": ["Profit and Loss Statement"],
  "decision": "execute"
}
```

Example:

```json
{
  "rule_id": "inventory_by_warehouse",
  "intent_class": "inventory_summary",
  "required_slots": {
    "inventory_axis": "warehouse"
  },
  "candidate_family_ids": ["inventory_snapshot"],
  "candidate_capability_ids": ["stock_read"],
  "candidate_reports": ["Warehouse Wise Stock Balance"],
  "decision": "execute"
}
```

Example:

```json
{
  "rule_id": "ranking_products_gross_profit",
  "intent_class": "ranked_entities",
  "required_slots": {
    "ranking_subject": "product",
    "ranking_metric": "gross_profit"
  },
  "candidate_family_ids": ["ranking_analytics"],
  "candidate_capability_ids": ["product_performance_read"],
  "candidate_reports": ["Gross Profit"],
  "decision": "execute"
}
```

### 7.5 Ambiguity Policies

Ambiguity must be explicit and governed.

Example:

```json
{
  "policy_id": "financial_statement_missing_variant",
  "intent_class": "financial_statement",
  "missing_slots": ["statement_variant"],
  "decision": "clarify",
  "reason_type": "semantic_slot_missing",
  "clarification_prompt_style": "choose_statement_variant"
}
```

## 8. Runtime Architecture Changes

### 8.1 `family_tool_surface.py`

Future role:

1. family scoring and discovery only
2. no report preference forcing
3. no family preference forcing for phrase-specific cases

This file may continue to expose:

1. candidate family ids
2. tool ids
3. family scoring rationale

It must not own:

1. report disambiguation policy
2. canonical alias routing
3. prompt-specific behavior corrections

### 8.2 `fresh_query_interpreter.py`

Future role:

1. call semantic interpretation
2. call semantic resolution
3. pass governed structured candidates to compiler

It must not:

1. override report candidates from phrase checks
2. patch family/report choice based on tactical narrowing

### 8.3 `compiler.py`

Compiler should consume:

1. candidate capability ids
2. candidate report ids
3. structured requested dimensions/metrics/time scope
4. explicit ambiguity state

Compiler should not be asked to guess around unresolved business-shape ambiguity.

## 9. Mini Phase Implementation Order

### Slice 1: Schema And Validation

Implement:

1. `qwen_semantic_resolution_contract`
2. builder in `contracts.py`
3. registry loader/validator for `semantic_resolution_registry.json`

Verification:

1. `py_compile`
2. guardrail audit
3. new unit tests for registry validation

### Slice 2: Financial Statement Resolution

Implement:

1. `statement_variant` slot extraction
2. financial statement resolution rules
3. replace canonical statement phrase routing with semantic slot resolution

Verification:

1. Tier 2
2. focused statement probes
3. wrapped regression

### Slice 3: Inventory Resolution

Implement:

1. `inventory_axis` slot extraction
2. inventory report resolution rules
3. replace inventory report disambiguation hacks with semantic slot resolution

Verification:

1. Tier 2
2. focused inventory probes
3. wrapped regression

### Slice 4: Ranking/Product Resolution

Implement:

1. `ranking_subject`
2. `ranking_metric`
3. governed ranking/product resolution rules

Verification:

1. Tier 2
2. Phase 4B ranking/product probes
3. wrapped regression

## 10. Success Criteria

This mini phase is successful when:

1. no runtime family/report routing depends on phrase-specific Python branches
2. statement aliases resolve through structured slot normalization and metadata rules
3. inventory axis resolution is governed by semantic slot state
4. ranking/product family resolution no longer relies on tactical narrowing
5. `family_tool_surface.py` is reduced to scoring/discovery behavior
6. Phase 4B governed-family latency smoke remains green without keyword patches

## 11. Explicit Non-Goals

This mini phase does not:

1. redesign the entire semantic runtime
2. replace ontology detection wholesale
3. expand every family at once
4. continue general-purpose refactoring of `service.py`

We pause broad refactoring until this routing architecture is corrected.

## 12. Decision Needed Before Implementation

One product-contract decision must be made before Slice 2:

1. Should `Which products are performing well last month` clarify between `Gross Profit` and `Item-wise Sales History`?

If yes:

1. keep the registry alignment already made
2. model it explicitly as semantic ambiguity between product-performance views

If no:

1. revert that registry alignment
2. define semantic rules that choose one governed report without clarification

This must be a product/governance choice, not an implementation convenience.
