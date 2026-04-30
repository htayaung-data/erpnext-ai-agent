# Qwen ERP Phase 4B Slice 1 Family Registry and Contracts Note (2026-03-22)

Status: completed  
Scope: Phase 4B Slice 1 from the Semantic Family Layer plan  
Slice goal: establish the shared family registry and typed contracts required for governed family routing, normalized business artifacts, and later composite read planning.

## Objective

This slice exists to prevent Phase 4B from drifting into ad hoc adapter code.

It establishes:

1. typed family-layer contracts
2. governed family registry metadata
3. ERP-side family metadata helpers
4. runtime-side family metadata helpers

This slice does not yet implement family adapters or composite execution behavior.

## What Was Implemented

### 1. New Phase 4B contracts

Added to [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py):

1. `ReportFamilyContract`
2. `NormalizedFamilyArtifactContract`
3. `CompositeReadPlanContract`
4. `FamilyValidationContract`

Added builder functions for all four so later slices can construct family-layer payloads through typed helpers instead of inline dictionaries.

### 2. New family registry metadata

Added [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json).

The initial governed family set now includes:

1. `financial_statement`
2. `aging`
3. `ranking_analytics`
4. `trend_analytics`
5. `inventory_snapshot`
6. `product_profitability`

Each family entry now defines:

1. supported intent classes
2. canonical metrics
3. canonical dimensions
4. adapter id
5. composite eligibility
6. governed capability ids and source reports
7. semantic tags and validation profile

### 3. ERP-side metadata helpers

Updated [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py) with helpers for:

1. loading the family registry
2. listing and resolving family specs
3. resolving governed family ids by report
4. resolving governed family ids by capability
5. reading canonical family metrics and dimensions
6. reading adapter ids, semantic tags, and validation profiles
7. listing family ids for a closed-set intent class

This keeps the next compiler and adapter work metadata-driven.

### 4. Runtime-side metadata helpers

Updated [report_registry.py](/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/report_registry.py) with runtime mirrors for:

1. loading the family registry
2. resolving family specs
3. resolving business family ids by report and capability
4. reading canonical family metrics and dimensions
5. reading family adapter ids and validation profiles

This preserves the shared ERP/runtime metadata boundary.

### 5. Metadata index update

Updated [README.md](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/README.md) so the family registry is now part of the documented shared metadata source of truth.

## What Was Intentionally Not Done Yet

This slice does **not** yet implement:

1. financial statement adapters
2. aging adapters
3. ranking/trend adapters
4. inventory/product profitability adapters
5. compiler-approved composite read plans at runtime
6. family-level semantic validation enforcement

Those belong to later Phase 4B slices.

## Verification Performed

Verified:

1. JSON validation passed for:
   - [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
   - [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
   - [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json)
   - [validation_rules.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/validation_rules.json)
2. Python compile passed for:
   - [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
   - [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py)
   - [report_registry.py](/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/report_registry.py)
3. ERP-side helper loading verified:
   - family count resolves to `6`
   - `Profit and Loss Statement` resolves to `financial_statement`
   - `sales_read` resolves to `ranking_analytics` and `trend_analytics`
4. runtime-side helper loading verified with `QWEN_ENTERPRISE_METADATA_DIR` set to the shared metadata path:
   - family count resolves to `6`
   - `Profit and Loss Statement` resolves to `financial_statement`
   - `sales_read` resolves to `ranking_analytics` and `trend_analytics`

## Architectural Result

Phase 4B now has a real metadata and contract foundation.

The system can now evolve from:

- governed reports

to:

- governed business families

without breaking the existing Phase 4 compiler and validator boundary.

## Exit Decision

Slice 4B.1 is:

- `completed`

## Next Slice

The next Slice 4B.2 work should implement the governed financial statement adapter path:

1. canonical financial statement schema
2. governed P&L adapter
3. governed Balance Sheet adapter
4. governed Cash Flow adapter
5. family-level validation for normalized financial statement artifacts
