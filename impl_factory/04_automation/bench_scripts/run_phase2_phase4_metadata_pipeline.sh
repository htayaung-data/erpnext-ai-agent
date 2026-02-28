#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/check_v7_contract_guardrails.py --root .

python3 impl_factory/04_automation/bench_scripts/phase2_capability_platform_refresh.py
python3 impl_factory/04_automation/bench_scripts/phase2_validate_capability_platform.py \
  --path impl_factory/04_automation/capability_v7/latest_capability_platform.json

python3 impl_factory/04_automation/bench_scripts/phase3_contract_overrides_refresh.py \
  --input-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --out-json impl_factory/04_automation/capability_v7/latest_contract_overrides.json
python3 impl_factory/04_automation/bench_scripts/phase3_validate_contract_overrides.py \
  --capability-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --overrides-json impl_factory/04_automation/capability_v7/latest_contract_overrides.json \
  --base-clarification-json impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/clarification_contract_v1.json

python3 impl_factory/04_automation/bench_scripts/phase4_db_semantic_catalog_refresh.py \
  --doctype-meta-json impl_factory/04_automation/logs/doctype_meta.json \
  --capability-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --out-json impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json
python3 impl_factory/04_automation/bench_scripts/phase4_validate_db_semantic_catalog.py \
  --path impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json

python3 impl_factory/04_automation/bench_scripts/phase5_ontology_refresh.py \
  --capability-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --db-semantic-json impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json \
  --out-json impl_factory/04_automation/capability_v7/latest_ontology_generated.json
python3 impl_factory/04_automation/bench_scripts/phase5_validate_ontology_generated.py \
  --path impl_factory/04_automation/capability_v7/latest_ontology_generated.json

python3 -m unittest \
  impl_factory/04_automation/bench_scripts/test_v7_constraint_engine.py \
  impl_factory/04_automation/bench_scripts/test_v7_semantic_resolver_constraints.py \
  impl_factory/04_automation/bench_scripts/test_v7_contract_registry.py \
  impl_factory/04_automation/bench_scripts/test_v7_clarification_policy.py \
  impl_factory/04_automation/bench_scripts/test_v7_quality_gate_constraints.py \
  impl_factory/04_automation/bench_scripts/test_v7_read_engine_clarification.py \
  impl_factory/04_automation/bench_scripts/test_v7_ontology_normalization.py \
  impl_factory/04_automation/bench_scripts/test_v7_db_semantic_catalog.py \
  impl_factory/04_automation/bench_scripts/test_phase3_contract_overrides_refresh.py \
  impl_factory/04_automation/bench_scripts/test_phase3_validate_contract_overrides.py \
  impl_factory/04_automation/bench_scripts/test_phase4_db_semantic_catalog_refresh.py \
  impl_factory/04_automation/bench_scripts/test_phase4_validate_db_semantic_catalog.py \
  impl_factory/04_automation/bench_scripts/test_phase5_ontology_refresh.py \
  impl_factory/04_automation/bench_scripts/test_phase5_validate_ontology_generated.py

echo "Phase2+Phase5 metadata pipeline: PASS"
