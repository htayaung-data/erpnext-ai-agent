#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/check_v7_contract_guardrails.py --root .

python3 impl_factory/04_automation/bench_scripts/phase5_ontology_refresh.py \
  --capability-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --db-semantic-json impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json \
  --out-json impl_factory/04_automation/capability_v7/latest_ontology_generated.json

python3 impl_factory/04_automation/bench_scripts/phase5_validate_ontology_generated.py \
  --path impl_factory/04_automation/capability_v7/latest_ontology_generated.json

python3 -m unittest \
  impl_factory/04_automation/bench_scripts/test_phase5_ontology_refresh.py \
  impl_factory/04_automation/bench_scripts/test_phase5_validate_ontology_generated.py \
  impl_factory/04_automation/bench_scripts/test_v7_ontology_normalization.py

echo "Phase5 ontology pipeline: PASS"
