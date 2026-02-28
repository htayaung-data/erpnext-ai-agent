#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/check_v7_contract_guardrails.py --root .

python3 impl_factory/04_automation/bench_scripts/phase4_db_semantic_catalog_refresh.py \
  --doctype-meta-json impl_factory/04_automation/logs/doctype_meta.json \
  --capability-json impl_factory/04_automation/capability_v7/latest_capability_platform.json \
  --out-json impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json

python3 impl_factory/04_automation/bench_scripts/phase4_validate_db_semantic_catalog.py \
  --path impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json

python3 -m unittest \
  impl_factory/04_automation/bench_scripts/test_phase4_db_semantic_catalog_refresh.py \
  impl_factory/04_automation/bench_scripts/test_phase4_validate_db_semantic_catalog.py \
  impl_factory/04_automation/bench_scripts/test_v7_db_semantic_catalog.py \
  impl_factory/04_automation/bench_scripts/test_v7_quality_gate_constraints.py

echo "Phase4 DB semantic catalog pipeline: PASS"
